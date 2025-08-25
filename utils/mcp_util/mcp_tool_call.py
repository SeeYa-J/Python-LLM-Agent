import asyncio
import json
import os
from contextlib import AsyncExitStack
from typing import Optional, Generator
from mcp import ClientSession
from utils.mcp_util.mysse import sse_client
from utils.mcp_util.util.apih_util import ApihUtil, config
from models.business_entities import BizUserStory
import re
from openai import OpenAI
from dao.user_dao import BizUserDAO
from config_service import ConfigService
from datetime import datetime, timedelta


class MCPCliente:
    def __init__(self, itcode: str):
        self.itcode = itcode
        config_service = ConfigService()
        self.user_dao = BizUserDAO(config_service.db_engine)
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.mcp_base_url = os.getenv("MCP_BASE_URL","https://apihub-test.lenovo.com/sit/v1/services/mcp-jira")  # Read MCP Base URL
        self.mcp_jira_token = self.user_dao.find_jira_token_by_itcode(self.itcode)
        self.maas_base_url = os.getenv("MAAS_BASE_URL","https://ai.ludp.lenovo.com/ics-apps/projects/115/qwen3-dev/aiverse/endpoint/v1")
        self.openai_api_key = os.getenv("OPENAI_API_MCP_KEY","sk-G8sqcwdyefe16ZJrVD6U8Z")  # Read OpenAI API Key
        self.server_params_list = []
        self.model = os.getenv("ENABLED_MCP_MODEL","Qwen3-32B")
        self.client = OpenAI(api_key=self.openai_api_key, base_url=self.maas_base_url)

        if not self.mcp_base_url:
            raise ValueError(" MCP Base URL not found, please set MCP_BASE_URL in .env file")
        if not self.mcp_jira_token:
            raise ValueError(" MCP JIRA Token not found, please set MCP_JIRA_TOKEN in .env file")

    async def connect_to_server(self):
        """通过 SSE 连接 MCP 服务器"""
        sse_transport = await self.exit_stack.enter_async_context(sse_client(
            base_url=self.mcp_base_url,
            url=self.mcp_base_url + "/sse",
            headers={
                "mcp-jira-personal-token": self.mcp_jira_token,
                "Authorization": "Bearer " + ApihUtil.get_new_token("CN"),
                "X-API-KEY": config['client_id']
            }
        ))
        sse, write = sse_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(sse, write))
        await self.session.initialize()
        response = await self.session.list_tools()
        tools = response.tools
        print(f"\nConnected to server {self.maas_base_url}, available tools:", [tool.name for tool in tools])

    async def create_jira_issue_from_data(self, jira_data: BizUserStory,project_key:str) -> str:
        additional_fields = {}

        priority = jira_data.jira_priority
        if priority:
            additional_fields["priority"] = {"name": priority}

        if jira_data.jira_story_points is not None:
            additional_fields["customfield_10002"] = jira_data.jira_story_points

        # 计划开始时间，默认当前时间
        planned_start = jira_data.jira_planned_start or datetime.now()
        additional_fields["customfield_10306"] = planned_start.strftime("%Y-%m-%dT%H:%M:%S.000+0800")

        # 计划结束时间，默认7天后
        planned_end = jira_data.jira_planned_end or (datetime.now() + timedelta(days=7))
        additional_fields["customfield_10902"] = planned_end.strftime("%Y-%m-%dT%H:%M:%S.000+0800")

        if jira_data.jira_acceptance_criteria is not None:
            additional_fields["customfield_10515"] = jira_data.jira_acceptance_criteria

        if jira_data.jira_ui_ux_design is not None:
            additional_fields["customfield_18301"] = jira_data.jira_ui_ux_design


        if jira_data.jira_background is not None:
            additional_fields["customfield_11490"] = jira_data.jira_background



        # 构建完整参数
        params = {
            "project_key": project_key,
            "issue_type": "Story",
            "summary": jira_data.jira_summary,
            "description": jira_data.jira_description,
            "additional_fields": json.dumps(additional_fields, ensure_ascii=False)
        }

        try:
            tool_result = await self.session.call_tool("jira_create_issue", params)
            result = tool_result.content[0].text
            return result
        except Exception as e:
            return f"创建失败: {str(e)}"

    async def update_jira_user_story(self, jira_data: BizUserStory,jira_key:str,project_key:str):
        update_fields = {}
        update_fields["assignee"]="zhongsz2"
        if jira_data.jira_priority:
            update_fields["priority"] = {"name": jira_data.jira_priority}

        if jira_data.jira_solution is not None:
            update_additional_fields = {
                "customfield_10302": jira_data.jira_solution
            }

        update_params = {
            "issue_key": jira_key,
            "fields": json.dumps(update_fields, ensure_ascii=False),
            "additional_fields": json.dumps(update_additional_fields, ensure_ascii=False)
        }

        await self.session.call_tool("jira_update_issue", update_params)

        if jira_data.jira_dependency:
            try:
                def extract_dependency_content(dependency_text):
                    dependency_text = dependency_text.strip()
                    if dependency_text.startswith("依赖于"):
                        return dependency_text[3:]  # 移除"依赖于"前缀
                    elif dependency_text.startswith("依赖"):
                        return dependency_text[2:]  # 移除"依赖"前缀
                    else:
                        return dependency_text  # 纯内容，直接返回

                search_content = extract_dependency_content(jira_data.jira_dependency)

                search_params = {
                    "jql": f"project = '{project_key}' AND text ~ '{search_content}'",
                    "limit": 10,
                    "fields": "summary,status,assignee,priority,created,updated"
                }

                search_result = await self.session.call_tool("jira_search", search_params)

                # 如果找到了相关的 issue，创建依赖关系
                if search_result and hasattr(search_result, 'content') and search_result.content:
                    result_text = search_result.content[0].text
                    result_data = json.loads(result_text)

                    # 如果找到了相关的 issue，创建依赖关系
                    if result_data.get("issues") and len(result_data["issues"]) > 0:
                        # 取第一个搜索结果作为依赖的 issue
                        dependency_issue_key = result_data["issues"][0]["key"]

                        # 创建 issue link (dependency_issue_key 依赖于 jira_key)
                        link_params = {
                            "link_type": "Duplicate",
                            "inward_issue_key": dependency_issue_key,  # 搜索到的 issue key
                            "outward_issue_key": jira_key  # 当前要更新的 issue key
                        }

                        await self.session.call_tool("jira_create_issue_link", link_params)
            except Exception:
                pass

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

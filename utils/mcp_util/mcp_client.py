import asyncio
import json
import os
from contextlib import AsyncExitStack
from typing import Optional, Generator
from mcp import ClientSession
from utils.mcp_util.mysse import sse_client
from utils.mcp_util.util.apih_util import ApihUtil, config
import re
from openai import OpenAI
from dao.user_dao import BizUserDAO
from config_service import ConfigService


class MCPClient:
    def __init__(self):
        config_service = ConfigService()
        self.user_dao = BizUserDAO(config_service.db_engine)
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.mcp_base_url = os.getenv("MCP_BASE_URL","https://apihub-test.lenovo.com/sit/v1/services/mcp-jira")  # Read MCP Base URL
        self.mcp_jira_token = self.user_dao.find_jira_token_by_itcode()
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

    def parse_tool_call(self, response: str) -> Optional[dict]:
        """
        从响应中提取 tool_call 字段的 JSON。
        """

        # 移除代码块标记（如```json）
        clean_response = re.sub(r"```.*?\n", "", response).strip()

        # 捕获所有 {} 块，使用堆栈方式避免正则复杂嵌套
        def extract_json_blocks(text):
            stack = []
            blocks = []
            start = None

            for i, char in enumerate(text):
                if char == '{':
                    if not stack:
                        start = i
                    stack.append(char)
                elif char == '}':
                    if stack:
                        stack.pop()
                        if not stack and start is not None:
                            blocks.append(text[start:i + 1])
            return blocks

        blocks = extract_json_blocks(clean_response)

        for idx, block in enumerate(blocks):
            try:
                parsed = json.loads(block)
                if isinstance(parsed, dict) and 'tool_call' in parsed:
                    return parsed['tool_call']
            except json.JSONDecodeError:
                continue

        raise ValueError("调用工具获取失败请重新尝试")

    async def process_query(self, query: str) -> str:
        # 这里需要通过 system prompt 来约束一下大语言模型，
        # 否则会出现不调用工具，自己乱回答的情况
        system_prompt = (
            "You are a helpful assistant."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]

        # 获取所有 mcp 服务器 工具列表信息
        response = await self.session.list_tools()
        # 生成 function call 的描述信息
        available_tools = [{
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            }
        } for tool in response.tools]

        # 请求 deepseek，function call 的描述信息通过 tools 参数传入
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=available_tools
        )

        # 处理返回的内容
        content = response.choices[0]
        while content.finish_reason == "tool_calls":
            # 如何是需要使用工具，就解析工具
            tool_call = content.message.tool_calls[0]
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            # 执行工具
            result = await self.session.call_tool(tool_name, tool_args)
            print(f"\n\n[Calling tool {tool_name} with args {tool_args}]\n\n")

            # 将 deepseek 返回的调用哪个工具数据和工具执行完成后的数据都存入messages中
            messages.append(content.message.model_dump())
            messages.append({
                "role": "tool",
                "content": result.content[0].text,
                "tool_call_id": tool_call.id,
            })

            # 将上面的结果再返回给 deepseek 用于生产最终的结果
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=available_tools
            )
            content = response.choices[0]

        return content.message.content

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()
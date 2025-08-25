# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0
from typing import List, Optional ,Dict
from config_service import ConfigService
from models.business_entities import BizJiraProject, BizDomain, BizUserStory,BizJiraUploadRecord
from dao.project_dao import BizJiraProjectDAO
from dao.domain_dao import BizDomainDAO
from dao.user_story_dao import BizUserStoryDAO
from dao.ai_prompt_dao import AiSystemPromptDAO
from dao.jira_upload_dao import BizJiraUploadRecordDAO
from dao.user_dao import BizUserDAO
from utils.dependency_injection import service
from utils.mcp_util.mcp_client import MCPClient
from utils.mcp_util.mcp_tool_call import MCPCliente
import asyncio
import json
import time
import requests
from utils.response_utils import ApiResponse
from config.context import current_itcode


@service
class JiraService:
    """Jira 相关业务服务层"""
    project_dao: BizJiraProjectDAO
    domain_dao: BizDomainDAO
    story_dao: BizUserStoryDAO
    prompt_dao: AiSystemPromptDAO
    user_dao: BizUserDAO
    jira_upload_record_dao: BizJiraUploadRecordDAO
    config_service: ConfigService

    # region ===== 项目相关 =====
    def create_project(self, data: dict, operator: str) -> BizJiraProject:
        return self.project_dao.create(BizJiraProject(**data), operator)

    def get_project_by_key(self, project_key: str) -> Optional[BizJiraProject]:
        return self.project_dao.find_by_project_key(project_key)

    def list_projects(self, page: int = 1, size: int = 20) -> List[BizJiraProject]:
        return self.project_dao.list_all(page, size)

    # endregion

    # region ===== 域相关 =====
    def create_domain(self, data: dict, operator: str) -> BizDomain:
        return self.domain_dao.create(BizDomain(**data), operator)

    def get_domain_by_code(self, domain_code: str) -> Optional[BizDomain]:
        return self.domain_dao.find_by_domain_code(domain_code)

    def list_domains(self, page: int = 1, size: int = 20) -> List[BizDomain]:
        return self.domain_dao.list_all(page, size)

    # endregion

    # region ===== Story 上传核心 =====
    def find_stories_for_upload(
            self,
            itcode: str,
            story_ids: List[int]
    ) -> List[BizUserStory]:

        if story_ids:
            return self.story_dao.find_for_upload(story_ids)
        else:
            return []

    # def upload_stories_to_jira(self, itcode: str, story_ids: list[int], project_id: int) -> dict:
    #     """上传用户故事到 JIRA，返回操作结果"""
    #     # client = MCPClient(itcode)
    #     client = MCPCliente(itcode)
    #     try:
    #         # 查找待上传的 Stories
    #         user_stories = self.story_dao.find_for_upload1(itcode, story_ids)
    #
    #         # 获取项目信息
    #         project_key = self.project_dao.find_by_project_id(project_id)
    #         if not project_key:
    #             return {
    #                 'success': False,
    #                 'message': f"项目 {project_id} 未找到",
    #                 'results': []
    #             }
    #
    #         if not user_stories:
    #             return {
    #                 'success': False,
    #                 'message': "没有找到待上传的用户故事",
    #                 'results': []
    #             }
    #
    #         results = []
    #         success_count = 0
    #
    #         for i, story in enumerate(user_stories):
    #             try:
    #                 # 添加时间间隔，除了第一个请求
    #                 if i > 0:
    #                     time.sleep(3)
    #
    #                 # 构造用户故事的可读格式
    #                 # story_dict = {
    #                 #     'summary': getattr(story, 'jira_summary', ''),
    #                 #     'description': getattr(story, 'jira_description', ''),
    #                 #     'acceptance_criteria': getattr(story, 'jira_acceptance_criteria', ''),
    #                 #     'priority': getattr(story, 'jira_priority', 'Medium'),
    #                 #     'story_points': getattr(story, 'jira_story_points', None),
    #                 #     'assignee': getattr(story, 'jira_assignee', ''),
    #                 #     'background': getattr(story, 'jira_background', ''),
    #                 #     'solution': getattr(story, 'jira_solution', ''),
    #                 #     'ui_ux_design': getattr(story, 'jira_ui_ux_design', ''),
    #                 #     'performance': getattr(story, 'jira_performance', ''),
    #                 #     'dependency': getattr(story, 'jira_dependency', ''),
    #                 #     'planned_start': getattr(story, 'jira_planned_start', None),
    #                 #     'planned_end': getattr(story, 'jira_planned_end', None)
    #                 # }
    #
    #                 # 构造用户输入
    #                 # serializable_payload = ApiResponse._serialize_data(story_dict)
    #                 # user_input = f"帮我把下列以给出的用户故事Issue type以story的形式插入JIRA中的{project_key}项目中：{json.dumps(serializable_payload, ensure_ascii=False)}"
    #                 story_id = story.id
    #                 # mcp_prompt = self.prompt_dao.find_by_id(60)[0].content
    #                 # filled_prompt = mcp_prompt.replace("{user_input}",user_input)
    #                 # 使用 _run_async_safely 来处理异步调用
    #                 # response = self._run_async_safely(client, filled_prompt)
    #                 response = self._run_async_safely(client, story, project_key)
    #                 # 提取JIRA Key
    #                 dict_jira = self.parse_jira_result_simple(response)
    #                 jira_key = dict_jira['issue_key']
    #                 url = f'https://jira.xpaas.lenovo.com/browse/{jira_key}'
    #                 summary = dict_jira['summary']
    #                 update_summary = f"[{jira_key}]{summary}"
    #                 create_time = dict_jira['create_time']
    #                 modify_time = dict_jira['modify_time']
    #                 modify_by = itcode
    #                 create_by = itcode
    #                 if jira_key:
    #                     self._silent_update_jira_issue(client, story, jira_key, project_key)
    #                     results.append({
    #                         'story_id': story_id,
    #                         'jira_project_id': project_id,
    #                         'status': '成功',
    #                         'jira_key': jira_key,
    #                         'url': url,
    #                         'summary': update_summary,
    #                         'create_time': create_time,
    #                         'modify_time': modify_time,
    #                         'modify_by': modify_by,
    #                         'create_by': create_by,
    #                     })
    #                     success_count += 1
    #                 else:
    #                     error_msg = dict_jira['error_msg']
    #                     results.append({
    #                         'story_id': story_id,
    #                         'jira_project_id': project_id,
    #                         'status': '失败',
    #                         'error_msg': error_msg,
    #                         'jira_key': None,
    #                         'url': None,
    #                         'create_time': None,
    #                         'modify_time': None,
    #                         'modify_by': None,
    #                         'create_by': None,
    #                     })
    #
    #             except Exception as e:
    #                 results.append({
    #                     'story_id': story_id,
    #                     'jira_project_id': project_id,
    #                     'status': '失败',
    #                     'error_msg': str(e),
    #                     'jira_key': None,
    #                     'url': None,
    #                     'create_time': None,
    #                     'modify_time': None,
    #                     'modify_by': None,
    #                     'create_by': None,
    #                 })
    #         try:
    #             upload_records = self.jira_upload_record_dao.batch_insert_upload_records(results)
    #             print(f"成功保存 {len(upload_records)} 条上传记录")
    #         except Exception as e:
    #             print(f"保存上传记录失败: {str(e)}")
    #
    #         if success_count > 0:
    #             update_result = self.story_dao.update_jira_id(itcode)
    #             if update_result['success']:
    #                 print(f"自动更新 jira_id 成功: {update_result['message']}")
    #             else:
    #                 print(f"自动更新 jira_id 失败: {update_result['message']}")
    #
    #         return {
    #             'success': success_count > 0,
    #             'message': f"上传完成，成功 {success_count}/{len(user_stories)} 个故事",
    #             'results': results,
    #             'total_count': len(user_stories),
    #             'success_count': success_count
    #         }
    #
    #     except Exception as e:
    #         return {
    #             'success': False,
    #             'message': f"上传过程中发生错误: {str(e)}",
    #             'results': []
    #         }
    #     finally:
    #         client.cleanup()

    # def _run_async_safely(self, client: MCPCliente, user_input: BizUserStory, project_key: str) -> str:
    #     """安全地运行异步代码，处理事件循环冲突"""
    #     import threading
    #     import queue
    #     import time
    #
    #     result_queue = queue.Queue()
    #     exception_queue = queue.Queue()
    #
    #     def run_in_thread():
    #         loop = None
    #         try:
    #             # 在新线程中创建新的事件循环
    #             loop = asyncio.new_event_loop()
    #             asyncio.set_event_loop(loop)
    #
    #             # 连接到服务器并处理查询
    #             loop.run_until_complete(client.connect_to_server())
    #             response = loop.run_until_complete(client.create_jira_issue_from_data(user_input, project_key))
    #             result_queue.put(response)
    #
    #         except Exception as e:
    #             exception_queue.put(e)
    #         finally:
    #             if loop and not loop.is_closed():
    #                 try:
    #                     # 优雅关闭连接
    #                     if hasattr(client, 'disconnect'):
    #                         loop.run_until_complete(client.disconnect())
    #
    #                     # 等待所有任务完成，而不是强制取消
    #                     pending = asyncio.all_tasks(loop)
    #                     if pending:
    #                         loop.run_until_complete(asyncio.wait_for(
    #                             asyncio.gather(*pending, return_exceptions=True),
    #                             timeout=5.0
    #                         ))
    #                 except Exception:
    #                     pass  # 忽略清理过程中的错误
    #                 finally:
    #                     loop.close()
    #
    #     # 在新线程中运行异步代码
    #     thread = threading.Thread(target=run_in_thread)
    #     thread.daemon = True
    #     thread.start()
    #     thread.join(timeout=60)  # 减少超时时间
    #
    #     # 检查是否有异常
    #     if not exception_queue.empty():
    #         raise exception_queue.get()
    #
    #     # 检查是否有结果
    #     if not result_queue.empty():
    #         return result_queue.get()
    #
    #     # 如果超时或没有结果
    #     raise TimeoutError("异步操作超时")

    # def parse_jira_result_simple(self, jira_text: str) -> Dict[str, str]:
    #     result = {}
    #
    #     try:
    #         # 提取JSON部分 - 从第一个{开始到最后一个}结束
    #         json_start = jira_text.find('{')
    #         json_end = jira_text.rfind('}') + 1
    #
    #         if json_start != -1 and json_end > json_start:
    #             json_text = jira_text[json_start:json_end].strip()
    #
    #             # 解析JSON数据
    #             data = json.loads(json_text)
    #
    #             # 提取所需字段
    #             result['status'] = 'Issue created successfully'
    #             result['issue_key'] = data.get('key', '')
    #             result['summary'] = data.get('summary', '')
    #             result['id'] = data.get('id', '')
    #             result['url'] = data.get('url', '').strip()
    #             result['description'] = data.get('description', '')
    #
    #             # 处理嵌套对象
    #             if 'status' in data and isinstance(data['status'], dict):
    #                 result['issue_status'] = data['status'].get('name', '')
    #                 result['status_category'] = data['status'].get('category', '')
    #
    #             if 'issue_type' in data and isinstance(data['issue_type'], dict):
    #                 result['issue_type'] = data['issue_type'].get('name', '')
    #
    #             if 'priority' in data and isinstance(data['priority'], dict):
    #                 result['priority'] = data['priority'].get('name', '')
    #
    #             if 'project' in data and isinstance(data['project'], dict):
    #                 result['project_key'] = data['project'].get('key', '')
    #                 result['project_name'] = data['project'].get('name', '')
    #
    #             if 'assignee' in data and isinstance(data['assignee'], dict):
    #                 result['assignee'] = data['assignee'].get('display_name', '')
    #
    #             if 'reporter' in data and isinstance(data['reporter'], dict):
    #                 result['reporter_name'] = data['reporter'].get('display_name', '')
    #                 result['reporter_email'] = data['reporter'].get('email', '')
    #
    #             # 时间字段
    #             result['create_time'] = data.get('created', '')
    #             result['modify_time'] = data.get('updated', '')
    #
    #     except Exception as e:
    #         result['error_msg'] = f"解析错误: {str(e)}"
    #
    #     return result

    # def _silent_update_jira_issue(self, client: MCPCliente, update_data: BizUserStory, jira_key: str,project_key: str):
    #     """静默更新 JIRA issue，不返回结果，不抛出异常"""
    #     import threading
    #
    #     def run_update():
    #         try:
    #             loop = asyncio.new_event_loop()
    #             asyncio.set_event_loop(loop)
    #
    #             try:
    #                 loop.run_until_complete(client.connect_to_server())
    #                 loop.run_until_complete(client.update_jira_user_story(update_data, jira_key,project_key))
    #             finally:
    #                 # 清理
    #                 pending = asyncio.all_tasks(loop)
    #                 for task in pending:
    #                     task.cancel()
    #                 try:
    #                     loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    #                 finally:
    #                     loop.close()
    #         except:
    #             # 静默处理所有异常
    #             pass
    #
    #     # 启动后台线程执行更新，不等待结果
    #     thread = threading.Thread(target=run_update)
    #     thread.daemon = True
    #     thread.start()

    def upload_stories_to_jira_by_api(self, itcode, story_ids, project_key,jira_token):
        # 查找待上传的 Stories
        user_stories: List[BizUserStory] = self.story_dao.find_for_upload1(itcode, story_ids)

        if not user_stories:
            return {
                'success': False,
                'message': "没有找到待上传的用户故事或用户故事已经上传过了",
                'results': []
            }

        req_data = []
        inner_req_data = {
            "project": project_key,
            "jira_token": jira_token,
            "issue_type": "Story",  # TODO:后面需要AI给出创建的东西，现在先固定story
            "components": [],  # TODO: 暂时不知道是什么，后面再加
            "assignee": current_itcode.get(),  # TODO: 后面取user_story.jira_assignee
        }

        biz_jira_upload_records = []
        for user_story in user_stories:
            biz_jira_upload_record = self._sycnhronize_user_story_to_jira(project_key, user_story, inner_req_data)
            biz_jira_upload_records.append(biz_jira_upload_record)

        return self._save_upload_records(biz_jira_upload_records)


    def _sycnhronize_user_story_to_jira(self, project_key: str, user_story: BizUserStory, inner_req_data: dict):
        inner_req_data["summary"] = user_story.jira_summary
        inner_req_data["description"] = user_story.jira_description
        inner_req_data["plannedstart"] = user_story.jira_planned_start.strftime('%Y-%m-%dT%H:%M:%S.000+0800')
        inner_req_data["plannedend"] = user_story.jira_planned_end.strftime('%Y-%m-%dT%H:%M:%S.000+0800')
        inner_req_data["background"] = user_story.jira_background
        inner_req_data["solution"] = user_story.jira_solution
        inner_req_data["acceptance_criteria"] = user_story.jira_acceptance_criteria
        inner_req_data["labels"] = ["AI_Solution"]

        url = self.config_service.data["jira_service_url"]
        resp_data = requests.post(url, json=[inner_req_data])
        try:
            resp_dict = json.loads(resp_data.text)[0]
            if resp_dict["key"]:
                upload_record = BizJiraUploadRecord(
                    story_id=user_story.id,
                    project_key=project_key,
                    jira_issue_key=resp_dict["key"],
                    url=f"https://jira.xpaas.lenovo.com/browse/{resp_dict['key']}",
                    status="成功",
                    error_msg=None,
                    create_by=user_story.create_by,
                    modify_by=user_story.modify_by,
                )
                return upload_record
            else:
               raise ValueError(f"JIRA API 返回错误: {resp_dict.get('error_msg', '未知错误')}")
        except Exception as e:
            return BizJiraUploadRecord(
                story_id=user_story.id,
                project_key=project_key,
                jira_issue_key=None,
                status="失败",
                error_msg=str(e),
                create_by=user_story.create_by,
                modify_by=user_story.modify_by,
            )


    def _save_upload_records(self, biz_jira_upload_records: List[BizJiraUploadRecord]) -> dict:
        success_count = 0
        dicts = []
        for biz_jira_upload_record in biz_jira_upload_records:
            if biz_jira_upload_record.status == "成功":
                success_count += 1
            biz_jira_upload_record_dict = biz_jira_upload_record.model_dump()
            dicts.append(biz_jira_upload_record_dict)

        try:
            upload_records = self.jira_upload_record_dao.batch_insert_upload_records2(biz_jira_upload_records)
            for biz_jira_upload_record in upload_records:
                update_res = self.story_dao.update_jira_id2(biz_jira_upload_record.story_id, biz_jira_upload_record.id)
                if not update_res:
                    print(f"自动更新 jira_id 失败: {biz_jira_upload_record.story_id} 的记录未找到")
            print(f"成功保存 {len(upload_records)} 条上传记录")
        except Exception as e:
            print(f"保存上传记录失败: {str(e)}")

        return {
            'success': success_count > 0,
            'message': f"上传完成，成功 {success_count}/{len(biz_jira_upload_records)} 个故事",
            'results': dicts,
            'total_count': len(biz_jira_upload_records),
            'success_count': success_count
        }
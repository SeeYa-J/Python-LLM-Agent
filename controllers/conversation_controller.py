import json
import uuid

from services.conversation_service import ConversationService
from services.project_service import ProjectService
from services.prompt_service import PromptService
from services.user_story_service import UserStoryService
from utils.dependency_injection import controller
from utils.response_utils import ApiResponse
import logging

@controller
class ConversationController:
    """用户对话控制器"""
    conversation_service: ConversationService
    user_story_service: UserStoryService
    prompt_service: PromptService
    project_service: ProjectService
    test_service_id = "1849753300972187648"
    optimus2_service_id = "1942161436139814912"

    def __init__(self):
        pass

    def judge_scenario(self, user_input: str) -> dict:
        """根据用户输入判断用户应用场景"""
        try:
            judge_user_scenarios_prompt = self.prompt_service.get_judge_user_scenarios_prompt(user_input)
            result = self.conversation_service.send_user_input_to_llm(self.optimus2_service_id,str(uuid.uuid1()),judge_user_scenarios_prompt)
            return ApiResponse.success(result, "用户应用场景判断成功")
        except Exception as e:
            return ApiResponse.error(f"用户应用场景判断失败: {str(e)}")

    def process_rewrite_user_story_send(self,
                             session_id: str,
                             conversation_id: int,
                             prompt_id: int,
                             round_number: int,
                             user_input: str,
                             operator: str,
                             project_key:str,
                             story_id:int=None)->dict:
        """处理修改用户故事对话"""
        try:
            # 插入对话详情表（用户）
            self.conversation_service.add_chat_session_detail(
                session_id=session_id,
                conversation_id=conversation_id,
                user_flag="1",
                user_input=user_input,
                prompt_id=prompt_id,
                round_number=round_number,
                operator=operator)
            print('插入对话详情表（用户）成功')
            # 根据story_id获取历史最新用户故事
            latest_user_story = self.user_story_service.get_user_story_by_story_id(story_id=story_id)
            print('获取历史用户故事成功')
            # 将用户故事转换成json格式
            latest_user_stories_json = self.user_story_service.get_json_user_story(user_stories=[latest_user_story])
            print('获取历史用户故事-json成功')
            # 获取生成用户故事提示词
            update_user_story_prompt = self.user_story_service.get_update_user_story_prompt(
                user_input=user_input,
                original_scheme=latest_user_stories_json)
            result = ""
            save_result = ""
            project = self.project_service.query_project_by_project_key(project_key)
            service_id = project.service_id
            for chunk in self.conversation_service.send_user_input_to_llm_v2(service_id=service_id,
                                                                             session_id=session_id,
                                                                             user_input=update_user_story_prompt):
                if "<think>" in result and chunk != "</think>" and "</think>" not in result:
                    save_result += chunk
                    yield json.dumps({"think": chunk}) + "\n\n"
                result += chunk

            if result == "":
                raise ValueError("AI FORCE返回出错，请稍后重试")
            print('获取llm回答成功')
            # 提取回答中的user_story数据
            user_story_str = self.conversation_service.get_special_data(llm_ans=result)
            print('获取user_story_str成功')
            # 格式化user_story
            user_story_list = self.user_story_service.get_user_story_by_json(user_story_str=user_story_str,
                                                                             operator=operator)
            print('获取user_story_list成功')
            # 引用文档保存
            result, rag_document_id = self.conversation_service.add_rag_doc(llm_ans=result, operator=operator)
            print('引用文档保存成功')
            # 插入对话详情表（llm）
            ai_chat_session_detail = self.conversation_service.add_chat_session_detail(
                session_id=session_id,
                conversation_id=conversation_id,
                user_flag="0",
                user_input=save_result,
                prompt_id=prompt_id,
                reg_document_id=str(rag_document_id),
                round_number=round_number,
                operator=operator)
            print('插入对话详情表（llm）成功')
            # 获取前端需要的数据
            return_data = self.conversation_service.get_update_user_story_api_return_data(user_story_list, result)
            print('获取前端需要的数据成功')
            data = json.dumps(ApiResponse.success(data=return_data, message="success",
                                                  conversation_id=conversation_id, session_id=session_id),
                              ensure_ascii=False)
            yield json.dumps({"body": data}) + "\n\n"
        except Exception as e:
            yield json.dumps({"body": ApiResponse.error(f"处理用户输入失败: {str(e)}")}) + "\n\n"

    def process_create_user_story_send(self,session_id: str,
                             conversation_id: int,
                             prompt_id: int,
                             round_number: int,
                             user_input: str,
                             operator: str,
                             project_key: str,
                             document_id: str=None)->dict:
        """处理用户生成用户故事对话"""
        try:
            # document绑定conversation
            self.conversation_service.set_document_conversation_id(document_id=document_id,
                                                                   conversation_id=conversation_id,
                                                                   operator=operator)
            print('document绑定conversation成功')
            # 插入对话详情表（用户）
            self.conversation_service.add_chat_session_detail(
                session_id=session_id,
                conversation_id=conversation_id,
                user_flag="1",
                user_input=user_input,
                prompt_id=prompt_id,
                ref_document_id=document_id,
                round_number=round_number,
                operator=operator)
            print('插入对话详情表（用户）成功')
            # 根据conversation_id获取历史最新用户故事
            latest_user_stories = self.user_story_service.get_latest_user_story_by_conversation_id(conversation_id=conversation_id,itcode=operator)
            print('获取历史用户故事成功')
            # 将用户故事转换成json格式
            latest_user_stories_json = self.user_story_service.get_json_user_story(user_stories=latest_user_stories)
            print('获取历史用户故事-json成功')
            # 获取生成用户故事提示词
            divide_user_story_prompt = self.user_story_service.get_divide_user_story_prompt(
                round_number=round_number,
                user_input=user_input,
                original_scheme=latest_user_stories_json)
            # 获取document内容 留待以后使用
            document_context = self.conversation_service.get_document_context(document_id=document_id)
            print('获取document内容成功')
            # 发送消息至llm，获取完整回答
            if round_number != 1:
                user_input = divide_user_story_prompt
            result = ""
            save_result = ""
            # 获取service_id
            project = self.project_service.query_project_by_project_key(project_key)
            service_id = project.service_id
            for chunk in self.conversation_service.send_user_input_to_llm_v2(service_id=service_id,
                                                                             session_id=session_id,
                                                                             user_input=user_input):
                if "<think>" in result and chunk != "</think>" and "</think>" not in result:
                    save_result += chunk
                    yield json.dumps({"think": chunk}) + "\n\n"
                result += chunk

            if result == "":
                raise ValueError("AI FORCE返回出错，请稍后重试")
            print('获取llm回答成功')
            # 提取回答中的user_story数据
            user_story_str = self.conversation_service.get_special_data(llm_ans=result)
            print('获取user_story_str成功')

            # 获取user_story整体概述
            user_story_prompt = self.prompt_service.get_user_story_summary_prompt(user_story_str)
            user_story_summary = self.conversation_service.send_user_input_to_llm(self.optimus2_service_id,
                                                                                  str(uuid.uuid1()), user_story_prompt)
            print('获取user_story整体概述成功')

            # 格式化user_story
            user_story_list = self.user_story_service.get_user_story_by_json(user_story_str=user_story_str,
                                                                             user_story_summary=user_story_summary,
                                                                             operator=operator)
            print('获取user_story_list成功')
            # 保存user_story至数据库
            user_stories = self.user_story_service.save_user_story(conversation_id=conversation_id,
                                                                   round_number=round_number,
                                                                   user_story_list=user_story_list,
                                                                   operator=operator)
            print('保存user_story至数据库成功')
            # 引用文档保存
            result, rag_document_id = self.conversation_service.add_rag_doc(llm_ans=result, operator=operator)
            print('引用文档保存成功')
            # 插入对话详情表（llm）
            self.conversation_service.add_chat_session_detail(
                session_id=session_id,
                conversation_id=conversation_id,
                user_flag="0",
                user_input=save_result,
                prompt_id=prompt_id,
                ref_document_id=document_id,
                reg_document_id=str(rag_document_id),
                round_number=round_number,
                operator=operator)
            print('插入对话详情表（llm）成功')
            # 获取前端需要的数据
            return_data = self.conversation_service.get_user_story_api_return_data(user_stories, result)
            print('获取前端需要的数据成功')
            data = json.dumps(ApiResponse.success(data=return_data, message="success",
                                                  conversation_id=conversation_id, session_id=session_id),
                              ensure_ascii=False)
            yield json.dumps({"body": data}) + "\n\n"
        except Exception as e:
            yield json.dumps({"body": ApiResponse.error(f"处理生成用户故事对话输入失败: {str(e)}")}) + "\n\n"

    def process_common_send(self,session_id: str,
                             conversation_id: int,
                             prompt_id: int,
                             round_number: int,
                             user_input: str,
                             service_id: str,
                             operator: str,
                             document_id: str=None)->dict:
        """处理用户普通对话"""
        try:
            # document绑定conversation
            self.conversation_service.set_document_conversation_id(document_id=document_id,
                                                                   conversation_id=conversation_id,
                                                                   operator=operator)
            print('document绑定conversation成功')
            # 插入对话详情表（用户）
            ai_chat_session_detail = self.conversation_service.add_chat_session_detail(
                session_id=session_id,
                conversation_id=conversation_id,
                user_flag="1",
                user_input=user_input,
                prompt_id=prompt_id,
                ref_document_id=document_id,
                round_number=round_number,
                operator=operator)
            print('插入对话详情表（用户）成功')
            # 获取document内容
            document_context = self.conversation_service.get_document_context(document_id=document_id)
            print('获取document内容成功')
            # 设置系统提示词
            llm_input = self.prompt_service.get_system_prompt(user_input=user_input,
                                                              document_context=document_context)
            print('设置系统提示词成功')
            # 发送消息至llm，获取完整回答
            result = ""
            save_result = ""
            for chunk in self.conversation_service.send_user_input_to_llm_v2(service_id=service_id,
                                                                             session_id=session_id,
                                                                             user_input=user_input):
                if "<think>" in result and chunk != "</think>" and "</think>" not in result:
                    save_result += chunk
                    yield json.dumps({"think": chunk}) + "\n\n"
                result += chunk
            print('获取llm成功')
            # 引用文档保存
            result, rag_document_id = self.conversation_service.add_rag_doc(llm_ans=result, operator=operator)
            print('引用文档保存成功')
            # 插入对话详情表（llm）
            ai_chat_session_detail = self.conversation_service.add_chat_session_detail(
                session_id=session_id,
                conversation_id=conversation_id,
                user_flag="0",
                user_input=save_result,
                prompt_id=prompt_id,
                ref_document_id=document_id,
                round_number=round_number,
                reg_document_id=str(rag_document_id),
                operator=operator)
            print('插入对话详情表（llm）成功')
            # 获取前端需要的数据
            return_data = self.conversation_service.get_user_story_api_return_data(None, result)
            print('获取前端需要的数据成功')
            data = json.dumps(ApiResponse.success(data=return_data, message="success",
                                                  conversation_id=conversation_id, session_id=session_id), ensure_ascii=False)
            yield json.dumps({"body": data}) + "\n\n"
        except Exception as e:
            yield json.dumps({"body": ApiResponse.error(f"处理用户普通对话输入失败: {str(e)}")}) + "\n\n"

    def list_user_chat(self,itcode: str,project_key: str) -> dict:
        """返回用户历史会话"""
        try:
            ai_chat_sessions = self.conversation_service.get_user_chats(itcode,project_key)
            return_data = self.conversation_service.get_user_chat_api_return_data(ai_chat_sessions)
            return ApiResponse.success(data=return_data, message="success")
        except Exception as e:
            return ApiResponse.error(f"返回用户历史会话失败: {str(e)}")

    def get_user_chat_detail(self,session_id: str,itcode: str) -> dict:
        """查询用户对话详情(itcode用于权限查询)"""
        try:
            chat_session,chat_session_details = self.conversation_service.get_user_chat_detail(session_id,itcode)
            return_data = self.conversation_service.get_user_chat_detail_api_return_data(chat_session,chat_session_details)
            return ApiResponse.success(data=return_data, message="success")
        except Exception as e:
            return ApiResponse.error(f"会话查询失败: {str(e)}")

    def upload_document(self,itcode: str,file_name: str,file_extension: str,content_bytes: bytes)->dict:
        """上传用户文档
        content_bytes：FastAPI读取的 文档bytes内容
        """
        try:
            # 检查文件名后缀
            if not self.conversation_service.check_upload_file_suffix(file_extension):
                raise ValueError("文档格式有误，支持的文档类型:docx、txt、pdf")
            # 获取文档内容，通过将 FastAPI读取的bytes转为utf-8
            document_context = self.conversation_service.analysis_document_context(file_extension=file_extension,
                                                                              content=content_bytes)
            # 保存文档到本地
            full_path,file_size = self.conversation_service.save_document(file_extension=file_extension,
                                                                          content=content_bytes,
                                                                          save_path="temp")
            # 插入上传文件表
            document = self.conversation_service.add_upload_document(file_name=file_name,
                                                                     save_path=full_path,
                                                                     file_size=file_size,
                                                                     file_extension=file_extension,
                                                                     file_context=document_context,
                                                                     operator=itcode)
            return_data = self.conversation_service.get_upload_document_api_return_data(document)
            return ApiResponse.success(data=return_data, message="success")
        except Exception as e:
            return ApiResponse.error(f"文档上传失败: {str(e)}")

    def delete_conversation(self,conversation_id: int,operator: str)->dict:
        """删除用户会话"""
        try:
            self.conversation_service.delete_conversation(conversation_id=conversation_id,operator=operator)
            return ApiResponse.success(message="success")
        except Exception as e:
            return ApiResponse.error(f"删除会话失败: {str(e)}")

    def init_conversation(self,project_key: str,
                            session_id: str,
                            user_input: str, # 用户输入内容
                            operator: str,
                            document_id: str=None,
                            scenario: str=None,
                            card_uuid: str=None)->dict:
        """创建或者修改用户会话"""
        try:
            # 从数据库 获取总结提示词 id=9
            summary_prompt = self.prompt_service.get_summary_prompt(user_input)
            ai_chat_session, prompt_id, round_number = self.conversation_service.init_session(
                                                                                    session_id=session_id,
                                                                                    project_key=project_key,
                                                                                    service_id=self.optimus2_service_id,
                                                                                    document_id=document_id,
                                                                                    operator=operator,
                                                                                    scenario=scenario,
                                                                                    user_input=summary_prompt,
                                                                                    card_uuid=card_uuid)
            data = self.conversation_service.get_init_conversation_return_data(conversation_id=ai_chat_session.id,
                                                                               session_id=ai_chat_session.session_id,
                                                                               round_number=round_number,
                                                                               prompt_id=prompt_id)
            return ApiResponse.success(data=data,message="success")
        except Exception as e:
            return ApiResponse.error(f"初始化会话失败: {str(e)}")



import json
import uuid

from services.agent_service import UserStoryChatAgentService
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
    agent_service: UserStoryChatAgentService
    test_service_id = "1849753300972187648"
    optimus2_service_id = "1942161436139814912"

    def __init__(self):
        pass

    def process_rewrite_user_story_send_v2(self,
                                        session_id: str,
                                        conversation_id: int,
                                        prompt_id: int,
                                        round_number: int,
                                        user_input: str,
                                        knowledge_base_id:int,
                                        story_id: int = None) -> dict:
        """处理修改用户故事对话"""
        try:
            for chunk in self.agent_service.graph_stream(session_id=session_id,
                                                         conversation_id=conversation_id,
                                                         prompt_id=prompt_id,
                                                         round_number=round_number,
                                                         user_input=user_input,
                                                         knowledge_base_id=knowledge_base_id,
                                                         story_id=story_id):
                yield chunk
        except Exception as e:
            yield json.dumps({"body": ApiResponse.error(f"修改用户故事失败: {str(e)}")}) + "\n\n"

    def process_create_user_story_send_by_agent(self,session_id: str,
                             conversation_id: int,
                             prompt_id: int,
                             round_number: int,
                             user_input: str,
                             knowledge_base_id: int,
                             document_ids: list[int]=None)->dict:
        """处理用户生成用户故事对话"""
        try:
            for chunk in self.agent_service.graph_stream(session_id=session_id,
                                                         conversation_id=conversation_id,
                                                         prompt_id=prompt_id,
                                                         round_number=round_number,
                                                         user_input=user_input,
                                                         knowledge_base_id=knowledge_base_id,
                                                         document_ids=document_ids):
                yield chunk
        except Exception as e:
            yield json.dumps({"body": ApiResponse.error(f"处理生成用户故事对话输入失败: {str(e)}")}) + "\n\n"


    def list_user_chat(self,project_key: str) -> dict:
        """返回用户历史会话"""
        try:
            ai_chat_sessions = self.conversation_service.get_user_chats(project_key)
            return_data = self.conversation_service.get_user_chat_api_return_data(ai_chat_sessions)
            return ApiResponse.success(data=return_data, message="success")
        except Exception as e:
            return ApiResponse.error(f"返回用户历史会话失败: {str(e)}")

    def get_user_chat_detail(self,session_id: str) -> dict:
        """查询用户对话详情(itcode用于权限查询)"""
        try:
            chat_session,chat_session_details = self.conversation_service.get_user_chat_detail(session_id)
            return_data = self.conversation_service.get_user_chat_detail_api_return_data(chat_session,chat_session_details)
            return ApiResponse.success(data=return_data, message="success")
        except Exception as e:
            return ApiResponse.error(f"会话查询失败: {str(e)}")

    def upload_document(self,file_name: str,file_extension: str,content_bytes: bytes)->dict:
        """上传用户文档"""
        try:
            # 检查文件名后缀
            if not self.conversation_service.check_upload_file_suffix(file_extension):
                raise ValueError("文档格式有误，支持的文档类型:docx、txt、pdf")
            # 获取文档内容
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
                                                                     file_context=document_context)
            return_data = self.conversation_service.get_upload_document_api_return_data(document)
            return ApiResponse.success(data=return_data, message="success")
        except Exception as e:
            return ApiResponse.error(f"文档上传失败: {str(e)}")

    def delete_conversation(self,conversation_id: int)->dict:
        """删除用户会话"""
        try:
            self.conversation_service.delete_conversation(conversation_id=conversation_id)
            return ApiResponse.success(message="success")
        except Exception as e:
            return ApiResponse.error(f"删除会话失败: {str(e)}")

    def init_conversation(self,project_key: str,
                            session_id: str,
                            user_input: str,
                            document_id: str=None,
                            # scenario: str=None,
                            card_uuid: str=None
                            )->dict:
        """创建或者修改用户会话"""
        try:
            # 获取总结提示词
            summary_prompt = self.prompt_service.get_summary_prompt(user_input)
            ai_chat_session, round_number = self.conversation_service.init_session(
                                                                                    session_id=session_id,
                                                                                    project_key=project_key,
                                                                                    service_id=self.optimus2_service_id,
                                                                                    document_id=document_id,
                                                                                    # scenario=scenario
                                                                                    user_input=summary_prompt,
                                                                                    card_uuid=card_uuid)
            data = self.conversation_service.get_init_conversation_return_data(conversation_id=ai_chat_session.id,
                                                                               session_id=ai_chat_session.session_id,
                                                                               round_number=round_number,
                                                                               # prompt_id=prompt_id
                                                                               )
            return ApiResponse.success(data=data,message="success")
        except Exception as e:
            return ApiResponse.error(f"初始化会话失败: {str(e)}")



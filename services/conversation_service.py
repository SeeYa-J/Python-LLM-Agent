import os
import re
import uuid
from typing import List, Optional

from config_service import ConfigService
from dao.ai_prompt_dao import AiSystemPromptDAO
from dao.chat_session_detail_dao import AiChatSessionDetailDAO
from dao.chat_session_dao import AiChatSessionDAO
from dao.document_dao import AiUploadDocumentDAO
from llms.aiforce_util import AiforceUtil
from models.business_entities import AiChatSession, AiChatSessionDetail, BizUserStory, AiAiforceRagDoc, AiUploadDocument
from utils.dependency_injection import service
import json

@service
class ConversationService:
    """处理conversation的服务层"""
    ai_prompt_dao: AiSystemPromptDAO
    document_dao: AiUploadDocumentDAO
    chat_session_dao:AiChatSessionDAO
    chat_session_detail_dao:AiChatSessionDetailDAO
    config_service:ConfigService

    def __init__(self):
        pass

    def init_session(self,
                     session_id:  str,
                     project_key: str,
                     service_id: str,
                     operator: str, #操作者
                     user_input: str,
                     scenario: str=None, #场景描述，用于确定提示词
                     card_uuid:str=None, #用户故事卡牌标识符
                     document_id: str=None) -> tuple[AiChatSession, int, int]:
        """初始化session_id以及历史会话表"""
        if not session_id: ### 创建会话
            chat_session_data = {} #session 相关数据 字典
            session_id = str(uuid.uuid1())# uuid1 基于MAC地址，时间戳，随机数来生成唯一的uuid
            chat_session_data["session_id"] = session_id
            chat_session_data["project_key"] = project_key
            # 获取用户第一轮对话的总结内容，生成会话摘要
            summary = AiforceUtil.get_all_result(user_input, service_id, str(uuid.uuid1()))
            chat_session_data["summary"] = summary
            status = "进行中"
            chat_session_data["status"] = status
            # 处理有用户上传文档的情况
            if document_id:
                chat_session_data["addition_info"] = document_id
            # 根据用户应用场景绑定提示词id
            if scenario == '生成 user story':
                prompt_id = self.config_service.data["prompt_id"]["divide_user_story_prompt_id"]
            elif scenario == '修改 user story':
                chat_session_data["user_story_uuid"] = card_uuid
                prompt_id = self.config_service.data["prompt_id"]["again_divide_user_story_prompt_id"]
            else:
                # 默认绑定
                prompt_id = self.config_service.data["prompt_id"]["divide_user_story_prompt_id"]
            # 创建会话对象
            chat_session = AiChatSession(**chat_session_data)
            round_number = 1
            return self.chat_session_dao.create(chat_session, operator),prompt_id,round_number
        else: ### 修改会话
            # 查询当前会话信息
            chat_session = self.chat_session_dao.query_chat_by_session_id(session_id)
            chat_session_details = self.chat_session_detail_dao.query_chat_detail_by_session_id(session_id)
            round_number = chat_session_details[0].round_number+1
            # 根据用户应用场景绑定提示词id
            if scenario == '生成 user story' or scenario == '修改 user story':
                prompt_id = self.config_service.data["prompt_id"]["again_divide_user_story_prompt_id"]
            else:
                # 默认绑定
                prompt_id = self.config_service.data["prompt_id"]["divide_user_story_prompt_id"]
            return chat_session,prompt_id,round_number

    def add_chat_session_detail(self,
                                session_id: str,
                                conversation_id:int,
                                user_flag: str,
                                user_input: str,
                                prompt_id: int,
                                round_number:  int,
                                operator: str,
                                ref_document_id: str = None,
                                reg_document_id: str = None)->AiChatSessionDetail:
        """创建对话详情数据"""
        chat_session_detail_data = {}
        chat_session_detail_data["session_id"] = session_id
        chat_session_detail_data["conversation_id"] = conversation_id
        chat_session_detail_data["user_flag"] = user_flag
        chat_session_detail_data["message_content"] = user_input
        if prompt_id:
            chat_session_detail_data["prompt_id"] = prompt_id
        if ref_document_id:
            chat_session_detail_data["ref_document_id"] = ref_document_id
        if reg_document_id:
            chat_session_detail_data["reg_document_id"] = reg_document_id
        chat_session_detail_data["round_number"] = round_number
        chat_session_detail = AiChatSessionDetail(**chat_session_detail_data)
        return self.chat_session_dao.create(chat_session_detail,operator)

    def send_user_input_to_llm(self,service_id: str,session_id,user_input: str) -> str:
        """发送用户输入至llm，返回llm完整回答"""
        return AiforceUtil.get_all_result(user_input,service_id,session_id)

    def send_user_input_to_llm_v2(self,service_id: str,session_id,user_input: str):
        """发送用户输入至llm，返回llm流式回答"""
        for chunk in AiforceUtil.chat(user_input,service_id,session_id):
            yield chunk

    def get_special_data(self,llm_ans: str) -> str:
        """解析AI回答中特殊标记过的数据"""
        special_data = {'csv', 'ppt', 'json', 'mermaid'}
        for flag in special_data:
            match = re.search(fr'</think>\s*```\s*{flag}', llm_ans)
            if match:
                # 获取匹配结束的位置
                end_pos = match.end()
                result = llm_ans[end_pos:].strip()
                match = re.search(f'```', result)
                if match:
                    start_pos = match.start()
                    result = result[:start_pos].strip()
                return result
        return ""

    def get_user_story_api_return_data(self,user_stories:List[BizUserStory]=None,ai_reply: str="")-> dict:
        """返回user_story卡片所需要的数据"""
        result = {}
        result["reply"] = ai_reply
        result["user_stories"] = []
        if not user_stories:
            return result
        for story in user_stories:
            data = {}
            data["story_id"] = story.id
            data["uuid"] = story.uuid
            data["jira_summary"] = story.jira_summary
            data["jira_description"] = story.jira_description
            data["jira_background"] = story.jira_background
            data["jira_acceptance_criteria"] = story.jira_acceptance_criteria
            data["jira_story_points"] = story.jira_story_points
            data["jira_priority"] = story.jira_priority
            data["jira_dependency"] = story.jira_dependency
            data["jira_performance"] = story.jira_performance
            data["jira_solution"] = story.jira_solution
            data["jira_ui_ux_design"] = story.jira_ui_ux_design
            data["jira_assignee"] = story.jira_assignee
            data["jira_planned_start"] = story.jira_planned_start
            data["jira_planned_end"] = story.jira_planned_end
            result["user_stories"].append(data)
        return result

    def get_user_chats(self,itcode: str,project_key: str)->List[AiChatSession]:
        """获取用户user_story_uuid为空的全部历史会话"""
        result = []
        chatSessions = self.chat_session_dao.query_chat_by_creator_and_project_key(itcode, project_key)
        for chatSession in chatSessions:
            if not chatSession.user_story_uuid or chatSession.user_story_uuid=="null":
                result.append(chatSession)
        return result

    def get_user_chat_api_return_data(self,ai_chat_sessions: List[AiChatSession])->dict:
        """返回用户历史会话所需要的数据"""
        result = {}
        result["total"] = len(ai_chat_sessions)
        result["conversations"] = []
        for ai_chat_session in ai_chat_sessions:
            data = {}
            data["conversation_id"] = ai_chat_session.id
            data["session_id"] = ai_chat_session.session_id
            data["summary"] = ai_chat_session.summary
            result["conversations"].append(data)
        return result

    def get_user_chat_detail(self,session_id,itcode)->tuple[AiChatSession,List[AiChatSessionDetail]]:
        """根据session_id以及itcode查询会话"""
        chat_session = self.chat_session_dao.query_chat_by_session_id(session_id)
        chat_details = self.chat_session_detail_dao.query_chat_detail_by_session_id(session_id)
        # for chat_detail in chat_details:
        #     if chat_detail.create_by != itcode:
        #         raise ValueError("当前用户无权限查看会话:"+session_id)
        return chat_session,chat_details

    def get_user_chat_detail_api_return_data(self,chat_session: AiChatSession,chat_session_details: List[AiChatSessionDetail])-> dict:
        """返回用户会话详情"""
        result = {}
        result["conversation_basic"] = {}
        result["conversation_basic"]["conversation_id"] = chat_session.id
        result["conversation_basic"]["summary"] = chat_session.summary
        result["history_messages"] = []
        ref_document_id = chat_session.addition_info
        ai_chat_session_details = []
        user_chat_session_details = []
        for i in range(len(chat_session_details) - 1, -1, -1):
            if chat_session_details[i].user_flag == '1':
                user_chat_session_details.append(chat_session_details[i])
            else:
                ai_chat_session_details.append(chat_session_details[i])
        for i in range(len(user_chat_session_details)):
            data = {}
            data["round_number"] = user_chat_session_details[i].round_number
            data["sender"] = "user"
            data["message_content"] = user_chat_session_details[i].message_content
            data["send_time"] = user_chat_session_details[i].create_time
            result["history_messages"].append(data)
            if i <len(ai_chat_session_details):
                data = {}
                data["round_number"] = ai_chat_session_details[i].round_number
                data["sender"] = "ai"
                data["message_content"] = ai_chat_session_details[i].message_content
                data["send_time"] = ai_chat_session_details[i].create_time
                result["history_messages"].append(data)
        result["mounted_files"] = []
        # 处理ref_document_id数组
        ref_documents_id=None
        if ref_document_id is not None and ref_document_id!="":
            # list_data = json.loads(ref_document_id)
            # ref_document_id = [int(item) for item in list_data]
            ref_documents_id=[]
            ref_documents_id.append(int(ref_document_id))
        if ref_documents_id:
            for document_id in ref_document_id:
                data = {}
                data["document_id"] = document_id
                document = self.document_dao.get_by_id(document_id)
                data["document_name"] = document.document_name
                result["mounted_files"].append(data)
        return result

    def add_rag_doc(self,llm_ans:str,operator: str)->tuple[str,List[int]]:
        """添加AIFORCE RAG文档，返回去除引用信息的回复以及document_id"""
        match = re.search(fr'<think>', llm_ans)
        rag_infos = []
        ans = ""
        documents_id = []
        if match:
            # 获取匹配结束的位置
            start_pos = match.start()
            end_pos = match.end()
            # 返回匹配结束位置之后的所有内容

            rag_infos = llm_ans[:start_pos].strip()
            if rag_infos != "":
                rag_infos = json.loads(rag_infos)
            ans = llm_ans[start_pos:].strip()
        for rag_info in rag_infos:
            document_data = {}
            document_data["file_name"] = rag_info["referenceDoc"]
            document_data["file_path"] = rag_info["referencePath"]
            document = AiAiforceRagDoc(**document_data)
            document_info = self.document_dao.create(document, operator)
            documents_id.append(document_info.id)
        if len(documents_id)==0:
            documents_id = None
        return ans,documents_id

    def check_upload_file_suffix(self,file_extension: str)->bool:
        """检查上传文档的类型是否是docx、txt、pdf"""
        if file_extension in ['.docx', '.txt', '.pdf']:
            return True
        return False

    def analysis_document_context(self,file_extension: str,content: bytes)->str:
        """获取文档中的文本内容"""
        if file_extension==".txt":
            content_str = content.decode('utf-8')
            return content_str

    def save_document(self,file_extension: str,content: bytes,save_path: str)->tuple[str,int]:
        """保存用户上传的文件"""
        # 确保临时目录存在
        if not os.path.exists(save_path):
            os.makedirs(save_path)  # 使用makedirs支持递归创建目录
        file_name = str(uuid.uuid1())
        full_path = os.path.join(save_path, file_name+file_extension)
        with open(full_path, 'wb') as f:
            f.write(content)
        # 获取文件大小（字节数）
        file_size = os.path.getsize(full_path)
        return full_path,file_size

    def add_upload_document(self,file_name: str, save_path: str
                            , file_size: int, file_extension: str,
                        file_context: str, operator: str)->AiUploadDocument:
        """保存用户上传文档至数据库"""
        document_data = {}
        document_data["document_name"] = os.path.splitext(file_name)[0]
        document_data["file_path"] = save_path
        document_data["file_size"] = file_size
        document_data["file_type"] = file_extension[1:]
        document_data["file_context"] = file_context
        document = AiUploadDocument(**document_data) # 数据库表对象document
        return self.document_dao.create(document,operator)#上传数据库

    def get_upload_document_api_return_data(self,document:AiUploadDocument)->dict:
        """返回上传文档前端所需数据"""
        data = {}
        data["document_id"] = document.id
        return data

    def get_document_context(self,document_id: str)->str:
        """通过数据库查询文档文本内容"""
        if document_id is not None:
            document_id = int(document_id)
            document = self.document_dao.get_by_id(document_id)
            return document.file_context
        return ""

    def set_document_conversation_id(self,document_id: str,conversation_id:int,operator: str)->bool:
        """设置文档会话id"""
        if document_id is not None:
            document_id = int(document_id)
            return self.document_dao.set_conversation_id(document_id,conversation_id,operator)
        return True

    def delete_conversation(self,conversation_id:id,operator:str)->bool:
        """删除会话以及会话详情"""
        chat_session = self.chat_session_dao.get_by_id(entity_id=conversation_id)
        chat_session_id = chat_session.session_id
        # 软删除会话表
        self.chat_session_dao.soft_delete(entity_id=conversation_id,operator=operator)
        chat_details = self.chat_session_detail_dao.query_chat_detail_by_session_id(chat_session_id)
        # 软删除会话详情表
        for chat_detail in chat_details:
            self.chat_session_detail_dao.soft_delete(chat_detail.id,operator)
        return True

    def get_init_conversation_return_data(self,conversation_id: int,session_id: str,round_number: int,prompt_id: int)->dict:
        """返回初始化会话前端所需数据"""
        data = {}
        data["conversation_id"] = conversation_id
        data["session_id"] = session_id
        data["round_number"] = round_number
        data["prompt_id"] = prompt_id
        return data

    def get_update_user_story_api_return_data(self,user_story_list: List[dict], ai_reply: str)->dict:
        """返回AI修改用户故事前端所需数据"""
        result = {}
        result["reply"] = ai_reply
        result["user_stories"] = []
        if not user_story_list:
            return result
        result["user_stories"].append(user_story_list[0])
        return result





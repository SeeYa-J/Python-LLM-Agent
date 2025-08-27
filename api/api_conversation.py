import os
import uuid
from typing import Optional

from fastapi import File, Form, UploadFile
from fastapi import Request, APIRouter, Depends
from config.constants import REQ_ROUTER
from controllers.conversation_controller import ConversationController
from llms.aiforce_util import AiforceUtil
from services.agent_service import UserStoryChatAgentService
from utils.dependency_injection import get_container
from pydantic import BaseModel, Field
from controllers.userstory_controller import UserStoryController
from fastapi.responses import StreamingResponse

class UserSendV1Request(BaseModel):
    conversation_id: int = Field(..., description="数据库标识会话id")
    prompt_id: int = Field(..., description="此次会话系统提示词id")
    round_number: int = Field(..., description="此次会话对话轮次")
    session_id: str = Field(..., description="AIFORCE会话id")
    message_content: str = Field(..., description="用户发送的消息")
    document_ids: int | list[int] = Field(None, description="挂载文件id")
    knowledge_base_id: str = Field(None, description="知识库id")

    class Config:
        json_schema_extra = {
            "example": {
                "itcode": "这是一个itcode",
                "conversation_id":1,
                "prompt_id":1,
                "round_number":1,
                "session_id": "AIFORCE会话id",
                "message_content": "这是一个用户输入示例",
                "document_ids": [123,456],
                "knowledge_base_id":"这是一个knowledge_base_Id"
            }
        }

class CreateConversationRequest(BaseModel):
    itcode: str = Field(..., description="用户it code")
    project_key: str = Field(..., description="project维度，和CMDB ID和知识库唯一绑定")
    session_id: str = Field(None, description="AIFORCE会话id")
    message_content: str = Field(..., description="用户发送的消息")
    document_id: int = Field(None, description="挂载文件id")

    class Config:
        json_schema_extra = {
            "example": {
                "itcode": "这是一个itcode",
                "project_key": "这是一个project_key",
                "session_id": "AIFORCE会话id",
                "message_content": "这是一个用户输入示例",
                "document_id": 1
            }
        }

class UserListRequest(BaseModel):
    itcode: str = Field(..., description="用户it code")
    project_key: str = Field(..., description="project维度，和CMDB ID和知识库唯一绑定")

    class Config:
        json_schema_extra = {
            "example": {
                "itcode": "这是一个itcode",
                "project_key": "这是一个project_key"
            }
        }

class UserChatDetailRequest(BaseModel):
    session_id: str = Field(..., description="会话session_id")
    itcode: str = Field(..., description="用户itcode用于权限检查")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "这是一个session_id",
                "itcode": "这是一个itcode"
            }
        }

class RewriteUserStoryRequestV1(BaseModel):
    story_id: int = Field(..., description="需要修改的user_story_id")
    card_uuid: str = Field(..., description="卡片的uuid")
    message_content: str = Field(..., description="用户需求")
    project_key: str = Field(..., description="project维度，和CMDB ID和知识库唯一绑定")
    prompt_id: int = Field(..., description="此次会话系统提示词id")
    session_id: str = Field(None, description="AI FORCE的session id")
    knowledge_base_id: str = Field(None, description="知识库id")

    class Config:
        json_schema_extra = {
            "example": {
                "story_id": 1,
                "card_uuid": "这是卡片的uuid",
                "message_content": "这是一个用户需求",
                "project_key": "这是一个project_key",
                "prompt_id":1,
                "session_id": "这是一个AI FORCE的session id",
                "knowledge_base_id": "这是一个knowledge_base_Id"
            }
        }

class DeleteConversationRequest(BaseModel):
    itcode: str = Field(..., description="用户itcode用于权限检查")
    conversation_id: int = Field(..., description="会话conversation_id")

    class Config:
        json_schema_extra = {
            "example": {
                "itcode": "这是一个itcode",
                "conversation_id": 1
            }
        }

class ApiConversation():
    """用户会话API模块"""

    def __init__(self, app):
        self.user_story_controller = get_container().get_bean(UserStoryController)
        self.conversation_controller = get_container().get_bean(ConversationController)
        self.agent = get_container().get_bean(UserStoryChatAgentService)
        self.agent.set_init()
        self._register_routes(app)

    def _register_routes(self, app):
        """注册所有API路由"""
        req = REQ_ROUTER
        router = APIRouter(
            prefix=req+"/conversation",
            tags=["User Conversation Management"],
        )

        @router.post("/list",
                     summary="获取用户全部历史会话",
                     description="根据用户itcode以及project_key获取用户全部历史会话(project_key可以为空)")
        def list_user_chat(
                user_list_request: UserListRequest
        ):
            """获取用户历史对话"""
            project_key = user_list_request.project_key
            return self.conversation_controller.list_user_chat(project_key=project_key)

        @router.post("/history",
                     summary="获取用户某个会话的会话详情",
                     description="根据session_id会话(itcode用于权限检查)")
        def get_user_chat_detail(
                user_chat_detail_request: UserChatDetailRequest
        ):
            """获取用户对话详情"""
            session_id = user_chat_detail_request.session_id
            return self.conversation_controller.get_user_chat_detail(session_id=session_id)

        @router.post("/rewrite-jira/v1",
                     summary="修改user_story(使用langgraph实现)",
                     description="按照用户需求修改指定user_story")
        def rewrite_user_story(
                rewrite_user_story_request: RewriteUserStoryRequestV1
        ):
            """ai修改user_story"""
            story_id = rewrite_user_story_request.story_id
            message_content = rewrite_user_story_request.message_content
            project_key = rewrite_user_story_request.project_key
            session_id = rewrite_user_story_request.session_id
            card_uuid = rewrite_user_story_request.card_uuid
            prompt_id = rewrite_user_story_request.prompt_id
            if rewrite_user_story_request.knowledge_base_id is not None:
                knowledge_base_id = int(rewrite_user_story_request.knowledge_base_id)
            else:
                knowledge_base_id = rewrite_user_story_request.knowledge_base_id
            # 初始化会话
            conversation_data = self.conversation_controller.init_conversation(project_key=project_key,
                                                                               session_id=session_id,
                                                                               user_input=message_content,
                                                                               card_uuid=card_uuid
                                                                               )
            session_id = conversation_data["data"]["session_id"]
            conversation_id = conversation_data["data"]["conversation_id"]
            round_number = conversation_data["data"]["round_number"]
            return StreamingResponse(
                self.conversation_controller.process_rewrite_user_story_send_v2(
                    session_id=session_id,
                    conversation_id=conversation_id,
                    prompt_id=prompt_id,
                    round_number=round_number,
                    user_input=message_content,
                    knowledge_base_id=knowledge_base_id,
                    story_id=story_id),
                media_type="text/event-stream",
                headers={
                    "Connection": "keep-alive",
                    "Content-Encoding": "none",
                    "Access-Control-Expose-Headers": "X-Chat-ID",
                },
            )

        @router.post("/document",
                     summary="用户上传文件",
                     description="用户上传相关领域知识")
        async def upload_user_document(
                file: UploadFile = File(...)
        ):
            """上传用户文档"""
            file_name = file.filename or "unknown_file"
            file_extension = os.path.splitext(file_name)[1].lower()
            content_bytes = await file.read()
            return self.conversation_controller.upload_document(file_name,file_extension,content_bytes)

        @router.post("/delete",
                     summary="删除用户会话",
                     description="根据conversation_Id删除用户会话")
        def delete_user_conversation(
                delete_conversation_request:DeleteConversationRequest
        ):
            """删除会话"""
            conversation_id = delete_conversation_request.conversation_id
            return self.conversation_controller.delete_conversation(conversation_id=conversation_id)

        @router.post("/send/v1",
                     summary="流式处理用户提问（langgraph实现）",
                     description="用户发送消息，对消息进行意图识别，如果用户需要生成user-story则生成卡片否则直接返回对话，并且保存此次会话信息（流式返回消息）")
        def process_user_send_v1(
                user_send_request: UserSendV1Request = None
        ):
            """处理用户提问"""
            conversation_id = user_send_request.conversation_id
            prompt_id = user_send_request.prompt_id
            round_number = user_send_request.round_number
            session_id = user_send_request.session_id
            user_input = user_send_request.message_content
            document_ids = user_send_request.document_ids
            if user_send_request.knowledge_base_id is not None:
                knowledge_base_id = int(user_send_request.knowledge_base_id)
            else:
                knowledge_base_id = user_send_request.knowledge_base_id
            # # 判断用户应用场景
            # scenario_info = self.conversation_controller.judge_scenario(user_input)
            # if not scenario_info["success"]:
            #     return scenario_info
            # scenario = scenario_info["data"]
            return StreamingResponse(
                self.conversation_controller.process_create_user_story_send_by_agent(
                    session_id=session_id,
                    conversation_id=conversation_id,
                    prompt_id=prompt_id,
                    round_number=round_number,
                    user_input=user_input,
                    document_ids=document_ids,
                    knowledge_base_id=knowledge_base_id),
                media_type="text/event-stream",
                headers={
                    "Connection": "keep-alive",
                    "Content-Encoding": "none",
                    "Access-Control-Expose-Headers": "X-Chat-ID",
                },
            )

        @router.post("/init",
                     summary="初始化用户会话",
                     description="初始化用户会话")
        async def create_user_conversation(
                create_conversation_request: CreateConversationRequest
        ):
            """创建会话"""
            project_key = create_conversation_request.project_key
            session_id = create_conversation_request.session_id
            message_content = create_conversation_request.message_content
            if create_conversation_request.document_id is not None:
                document_id = str(create_conversation_request.document_id)
            else:
                document_id = create_conversation_request.document_id
            return self.conversation_controller.init_conversation(project_key=project_key,
                                                                    session_id=session_id,
                                                                    user_input=message_content,
                                                                    document_id=document_id)

        app.include_router(router)

import os
import uuid
from typing import Optional

from fastapi import File, Form, UploadFile # 处理文件上传和表单数据。
from fastapi import Request, APIRouter, Depends # 获取HTTP请求信息、创建路由、依赖注入
from config.constants import REQ_ROUTER
from controllers.conversation_controller import ConversationController
from utils.dependency_injection import get_container
from pydantic import BaseModel, Field
from controllers.userstory_controller import UserStoryController
from fastapi.responses import StreamingResponse

## FastAPI框架实现的Agent API模块，主要处理用户会话管理和AI交互功能
## 全是Pydantic
'''
关键组件解析​​：
    fastapi：Web框架，用于构建API
    pydantic：数据验证和设置管理
    StreamingResponse：流式响应，用于实时返回AI生成的内容
    get_container：依赖注入容器（类似Spring的IoC容器）
    ConversationController和UserStoryController：业务逻辑控制器
'''
## 使用 Pydantic 模型验证数据结构,即 入参格式要符合 Pydantic
class UserSendV2Request(BaseModel):
    itcode: str = Field(..., description="用户it code")
    conversation_id: int = Field(..., description="数据库标识会话id")
    prompt_id: int = Field(..., description="此次会话系统提示词id")
    round_number: int = Field(..., description="此次会话对话轮次")
    session_id: str = Field(..., description="AIFORCE会话id")
    message_content: str = Field(..., description="用户发送的消息")
    document_id: int = Field(None, description="挂载文件id")
    project_key: str = Field(..., description="project维度，和CMDB ID和知识库唯一绑定")

    # FastAPI会自动从Pydantic模型生成OpenAPI/Swagger文档
    # Config类中的schema_extra属性提供的示例值会直接显示在API文档中，
    # 这样在文档中就会显示这些示例值，帮助API使用者理解如何构造请求。
    class Config:
        json_schema_extra = {
            "example": {
                "itcode": "这是一个itcode",
                "conversation_id":1,
                "prompt_id":1,
                "round_number":1,
                "session_id": "AIFORCE会话id",
                "message_content": "这是一个用户输入示例",
                "document_id": 1,
                "project_key": "这是一个project_key"
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

class RewriteUserStoryRequest(BaseModel):
    itcode: str = Field(..., description="用户itcode")
    story_id: int = Field(..., description="需要修改的user_story_id")
    card_uuid: str = Field(..., description="卡片的uuid")
    message_content: str = Field(..., description="用户需求")
    project_key: str = Field(..., description="project维度，和CMDB ID和知识库唯一绑定")
    session_id: str = Field(None, description="AI FORCE的session id")

    class Config:
        json_schema_extra = {
            "example": {
                "itcode": "这是一个itcode",
                "story_id": 1,
                "card_uuid": "这是卡片的uuid",
                "message_content": "这是一个用户需求",
                "project_key": "这是一个project_key",
                "session_id": "这是一个AI FORCE的session id"
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


"""用户会话API模块，基于conversation_controller进行会话管理"""
class ApiConversation():
    """用户会话API模块"""

    def __init__(self, app):
        ## 初始化bean、路由
        self.user_story_controller = get_container().get_bean(UserStoryController)
        self.conversation_controller = get_container().get_bean(ConversationController)
        self._register_routes(app)

    def _register_routes(self, app):
        """注册所有API路由"""
        req = REQ_ROUTER #"/api/req"
        router = APIRouter(
            prefix=req+"/conversation", #统一前缀，req/conversation
            tags=["User Conversation Management"],#分组标签
        )

        @router.post("/list",
                     summary="获取用户全部历史会话",# summary提供断点描述
                     description="根据用户itcode以及project_key获取用户全部历史会话(project_key可以为空)")
        def list_user_chat( #Pydantic自动验证格式
                user_list_request: UserListRequest
        ):
            """获取用户历史对话"""
            itcode = user_list_request.itcode # 用户itcode
            project_key = user_list_request.project_key #
            return self.conversation_controller.list_user_chat(itcode=itcode,project_key=project_key)

        @router.post("/history",
                     summary="获取用户某个会话的会话详情",
                     description="根据session_id会话(itcode用于权限检查)")
        def get_user_chat_detail(
                user_chat_detail_request: UserChatDetailRequest
        ):
            """获取用户对话详情"""
            session_id = user_chat_detail_request.session_id
            itcode = user_chat_detail_request.itcode
            return self.conversation_controller.get_user_chat_detail(session_id=session_id,itcode=itcode)

        @router.post("/rewrite-jira",
                     summary="修改user_story",
                     description="按照用户需求修改指定user_story")
        def rewrite_user_story( #TODO: 网络调用统一改成httpx以支持异步而非同步忙等
                rewrite_user_story_request: RewriteUserStoryRequest
        ):
            """ai修改user_story"""
            itcode = rewrite_user_story_request.itcode
            story_id = rewrite_user_story_request.story_id
            message_content = rewrite_user_story_request.message_content
            project_key = rewrite_user_story_request.project_key
            session_id = rewrite_user_story_request.session_id
            card_uuid = rewrite_user_story_request.card_uuid
            scenario = "修改 user story"
            # 初始化会话 #在card
            conversation_data = self.conversation_controller.init_conversation(project_key=project_key,
                                                                    session_id=session_id,
                                                                    user_input=message_content,
                                                                    operator=itcode,
                                                                    scenario=scenario,
                                                                    card_uuid=card_uuid
                                                                    )
            session_id = conversation_data["data"]["session_id"]
            conversation_id = conversation_data["data"]["conversation_id"]
            prompt_id = conversation_data["data"]["prompt_id"]
            round_number = conversation_data["data"]["round_number"]
            return StreamingResponse(
                self.conversation_controller.process_rewrite_user_story_send(
                                                                  session_id=session_id,
                                                                  conversation_id=conversation_id,
                                                                  prompt_id=prompt_id,
                                                                  round_number=round_number,
                                                                  user_input=message_content,
                                                                  story_id=story_id,
                                                                  project_key=project_key,
                                                                  operator=itcode),
                media_type="text/event-stream",
                headers={
                    "Connection": "keep-alive",
                    "Content-Encoding": "none",
                    "Access-Control-Expose-Headers": "X-Chat-ID",
                },
            )

        @router.post("/document",
                     summary="用户上传文件",
                     description="异步 用户上传相关领域知识")
        async def upload_user_document(
                itcode: str,file: UploadFile = File(...) #...表示必选参数
        ):
            ## UploadFile 属性：.filename，.content_type，.size，.headers
            """上传用户文档"""
            file_name = file.filename or "unknown_file"
            file_extension = os.path.splitext(file_name)[1].lower()
            content_bytes = await file.read() # 读取文档
            return self.conversation_controller.upload_document(itcode,file_name,file_extension,content_bytes)

        @router.post("/delete",
                     summary="删除用户会话",
                     description="根据conversation_Id删除用户会话")
        def delete_user_conversation(
                delete_conversation_request:DeleteConversationRequest
        ):
            """删除会话"""
            itcode = delete_conversation_request.itcode
            conversation_id = delete_conversation_request.conversation_id
            return self.conversation_controller.delete_conversation(conversation_id=conversation_id,operator=itcode)

        @router.post("/send/v2",
                     summary="流式处理用户提问",
                     description="用户发送消息，对消息进行意图识别，如果用户需要生成user-story则生成卡片否则直接返回对话，并且保存此次会话信息（流式返回消息）")
        def process_user_send_v2(
                user_send_request: UserSendV2Request = None
        ):
            """处理用户提问"""
            itcode = user_send_request.itcode
            conversation_id = user_send_request.conversation_id
            prompt_id = user_send_request.prompt_id
            round_number = user_send_request.round_number
            session_id = user_send_request.session_id
            user_input = user_send_request.message_content
            document_id = user_send_request.document_id
            project_key = user_send_request.project_key
            # 处理document_id
            if document_id is not None:
                document_id = str(document_id)
            # # 判断用户应用场景
            # scenario_info = self.conversation_controller.judge_scenario(user_input)
            # if not scenario_info["success"]:
            #     return scenario_info
            # scenario = scenario_info["data"]
            return StreamingResponse(
                self.conversation_controller.process_create_user_story_send(
                    session_id=session_id,
                    conversation_id=conversation_id,
                    prompt_id=prompt_id,
                    round_number=round_number,
                    user_input=user_input,
                    document_id=document_id,
                    project_key=project_key,
                    operator=itcode),
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
            itcode = create_conversation_request.itcode
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
                                                                    document_id=document_id,
                                                                    operator=itcode)

        app.include_router(router)

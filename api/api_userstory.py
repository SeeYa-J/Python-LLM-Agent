# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
from fastapi import Request, APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from controllers.userstory_controller import UserStoryController
from utils.dependency_injection import get_container
from fastapi import HTTPException, status
from config.constants import REQ_ROUTER
from fastapi.responses import FileResponse
from config.context import current_itcode


class AiPromptCreateRequest(BaseModel):
    itcode: Optional[str] = Field(None, description="ITCode")
    project_key: str = Field(..., description="project维度，和CMDB ID和知识库唯一绑定")
    domain_id: int = Field(..., description="领域ID")
    title: str = Field(..., description="提示词标题")
    content: str = Field(..., description="提示词内容")
    description: Optional[str] = Field(None, description="提示词描述")

    class Config:
        json_schema_extra = {
            "example": {
                "itcode": "test_user",
                "project_key": "这是一个project_key",
                "domain_id": 2,
                "title": "示例提示词",
                "content": "这是一个提示词内容示例",
                "description": "提示词描述"
            }
        }


class AiPromptUpdateRequest(BaseModel):
    itcode: Optional[str] = Field(None, description="ITCode")
    prompt_id: int = Field(..., description="提示词ID")
    title: Optional[str] = Field(None, description="提示词标题")
    content: Optional[str] = Field(None, description="提示词内容")
    description: Optional[str] = Field(None, description="提示词描述")
    class Config:
        json_schema_extra = {
            "example": {
                "itcode": "test_user",
                "prompt_key": "这是一个project_key",
                "title": "更新后的提示词标题 - 可选",
                "content": "更新后的提示词内容 - 可选",
                "description": "更新后的描述 - 可选",
            }
        }


class AiPromptGetRequest(BaseModel):
    itcode: Optional[str] = Field(None, description="ITCode")
    prompt_id: int = Field(..., description="提示词ID")

    class Config:
        json_schema_extra = {
            "example": {
                "itcode": "test_user",
                "prompt_id": 1
            }
        }


class AiPromptDeleteRequest(BaseModel):
    itcode: Optional[str] = Field(None, description="ITCode")
    prompt_id: int = Field(..., description="提示词ID")

    class Config:
        json_schema_extra = {
            "example": {
                "itcode": "test_user",
                "prompt_id": 1
            }
        }

#2025.8.12 这边已经改为从context取itcode维度查询list，为了稳定保留project_key字段
class PromptsListRequest(BaseModel):
    itcode: Optional[str] = Field(None, description="ITCode")
    project_key: Optional[str] = Field(None, description="project维度，和CMDB ID和知识库唯一绑定")
    is_predefined: Optional[bool] = Field(None, description="是否为预定义提示词，默认为False")
    class Config:
        json_schema_extra = {
            "example": {
                "itcode": "test_user",
                "is_predefined": "null"  # 是否为预定义提示词，默认为False
            }
        }

class GetUserStoryRequest(BaseModel):
    """
    获取用户故事请求参数
    """
    itcode: str = Field(..., description="用户工号/登录账号")
    session_id: str = Field(..., description="AIFORCE 会话 ID")

    class Config:
        json_schema_extra = {
            "example": {
                "itcode": "zhangsan",
                "session_id": "sess-xxx-123"
            }
        }

class UploadToJiraRequest(BaseModel):
    itcode: str = Field(..., description="操作人工号")
    story_ids: List[int] = Field(..., description="要上传的 story_id 列表")
    project_key: str = Field(description="项目名字SMTGETCS")
    jira_token: str = Field(description="jira的token")


    class Config:
        json_schema_extra = {
            "example": {
                "itcode": "zhangsan",
                "story_ids": [4001, 4002],
                "project_key": "smtgetcs",
                "jira_token": "123344412ada"
            }
        }

class UpdateUserStroyRequest(BaseModel):
    itcode: str = Field(..., description="操作者工号")
    uuid: str = Field(..., description="标识单个卡片的id")
    jira_summary: Optional[str] = Field(None, description="用户故事的标题")
    jira_description:Optional[str] = Field(None, description="描述")
    jira_acceptance_criterta: Optional[str] = Field(None, description="验收标准")
    jira_background: Optional[str] = Field(None, description="背景介绍")
    jira_story_points: Optional[int] = Field(None, description="预估故事点")
    jira_priority: Optional[str] = Field(None, description="优先级")
    jira_dependency: Optional[str] = Field(None, description="依赖项")
    jira_performence: Optional[str] = Field(None, description="表现")
    jira_solution: Optional[str] = Field(None, description="解决方案")
    jira_ui_ux_design: Optional[str] = Field(None, description="界面设计")
    jira_assignee: Optional[str] = Field(None, description="assignee")
    jira_planned_start: Optional[str] = Field(None, description="计划开始时间")
    jira_planned_end: Optional[str] = Field(None, description="计划结束时间")

    def to_story_data_dict(self) -> Dict[str, Any]:
        """将请求对象转换为story_data字典，排除itcode和uuid"""
        return self.dict(exclude={'itcode', 'uuid'}, exclude_unset=True)

    class Config:
        json_schema_extra = {
            "example": {
                "itcode": "zhangsan",
                "uuid": "123",
                "jira_summary": "作为用户，我希望…",
                "jira_description": "用户故事的详细描述",
                "jira_acceptance_criterta": "1. 功能正常\n2. 满足性能要求",
                "jira_background": "背景信息",
                "jira_story_points": 5,
                "jira_priority": "High",
                "jira_dependency": "依赖服务 A",
                "jira_performence": "响应时间 < 1s",
                "jira_solution": "采用方案 X 实现",
                "jira_ui_ux_design": "链接到设计稿",
                "jira_assignee": "lisi",
                "jira_planned_start": "2025-07-20",
                "jira_planned_end": "2025-07-30"
            }
        }

class ExhibitUserStoryRequest(BaseModel):
    itcode: str = Field(..., description="操作者工号")
    conversation_id: int = Field(..., description="AIFORCE对话记录ID")

    class Config:
        json_schema_extra = {
            "example": {
                "itcode": "zhangsan",
                "conversation_id":5
            }
        }

class DeleteUserStoryRequest(BaseModel):
    itcode: str = Field(..., description="操作者工号")
    uuids: List[str] = Field(..., description="要删除的用户故事uuid列表")

    class Config:
        json_schema_extra = {
            "example": {
                "itcode": "zhangsan",
                "uuids": ["123", "456"]
            }
        }

class DownloadUserStoryRequest(BaseModel):
    """下载用户故事请求模型"""
    itcode: str = Field(..., description="操作者工号")
    uuids: List[str] = Field(..., description="要下载的用户故事uuid列表")

    class Config:
        json_schema_extra = {
            "example": {
                "itcode": "zhangsan",
                "uuids": ["123", "456"]
            }
        }

class ApiUserStory():
    """用户故事API模块"""

    def __init__(self, app):
        self.controller: UserStoryController = get_container().get_bean(UserStoryController)
        self._register_routes(app)

    def _register_routes(self, app):
        """注册所有API路由"""
        req = REQ_ROUTER
        router = APIRouter(
            prefix= req + "/userstory",
            tags=["User Story Management"],#修改了swagger名称
        )

        @router.post("/prompts/create",
                    summary="创建AI系统提示词",
                    description="创建新的AI系统提示词并返回创建的提示词详情")
        def create_ai_prompt(
            prompt_request: AiPromptCreateRequest,
            request: Request
        ):
            """创建AI系统提示词"""
            if(current_itcode.get()):
                operator = current_itcode.get()
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="操作人ITCode不能为空"
                )
            return self.controller.create_ai_prompt(
                prompt_request.model_dump()
            )

        @router.post("/prompts/get",
                    summary="获取AI系统提示词详情",
                    description="通过提示词ID获取AI系统提示词详细信息")
        def get_ai_prompt(prompt_request: AiPromptGetRequest):
            """获取AI系统提示词详情"""
            if(current_itcode.get()):
                operator = current_itcode.get()
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="操作人ITCode不能为空"
                )
            return self.controller.get_ai_prompt(prompt_request.prompt_id)

        @router.post("/prompts/list",
                    summary="获取项目提示词列表",
                    description="根据itcode获取该用户的所有提示词列表")
        def list_prompts_by_itcode(project_request: PromptsListRequest):
            """根据项目ID获取提示词列表"""
            if(current_itcode.get()):
                operator = current_itcode.get()
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="操作人ITCode不能为空"
                )
            is_predefined = project_request.is_predefined
            return self.controller.list_prompts_by_itcode(operator, project_request.is_predefined)

        @router.post("/prompts/predefined",
                    summary="获取预制提示词列表",
                    description="获取系统中所有预制的提示词列表")
        async def list_predefined_prompts():
            """获取预制提示词列表"""
            return self.controller.list_predefined_prompts()

        @router.post("/prompts/update",
                    summary="更新AI系统提示词",
                    description="更新指定ID的AI系统提示词内容、描述或其他属性")
        
        def update_ai_prompt(
            prompt_request: AiPromptUpdateRequest,
            request: Request
        ):

            """更新AI系统提示词"""
            if(current_itcode.get()):
                operator = current_itcode.get()
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="操作人ITCode不能为空"
                )
            # 提取prompt_id和更新数据
            prompt_id = prompt_request.prompt_id

            existing_prompt_message = self.controller.get_ai_prompt(prompt_id)
            existing_prompt = existing_prompt_message['data']

            # 使用 exclude_unset=True 来区分未传送的字段和传来空值的字段
            provided_fields = prompt_request.model_dump(exclude_unset=True)

            # 过滤掉prompt_id和未提供的字段

            update_data = {k: v for k, v in provided_fields.items()
                        if k != 'prompt_id'}

            if existing_prompt.get('is_predefined', False):
                # 如果是预定义提示词，创建一个新的记录
                # 这个记录要复制已有的预定义提示词内容
                # 创建新的提示词请求

                base_data = {
                    "project_key": existing_prompt['project_key'],
                    "domain_id": existing_prompt['domain_id'],
                    "title": existing_prompt['title'],
                    "content": existing_prompt['content'],
                    "is_predefined": False, # 新创建的提示词不再是预定义的
                    "description": existing_prompt.get('description', '')
                }

                base_data.update(update_data)
                return self.controller.create_ai_prompt(
                    base_data,
                    operator
                )

            else:

                return self.controller.update_ai_prompt(
                    prompt_id,
                    update_data,
                    operator
                )

        @router.post("/prompts/delete",
                    # response_model=Dict[str, Any],
                    summary="删除AI系统提示词",
                    description="删除指定ID的AI系统提示词")
        def delete_ai_prompt(
            delete_request: AiPromptDeleteRequest,
            request: Request
        ):
            """删除AI系统提示词"""
            if(current_itcode.get() is None):
                operator = AiPromptDeleteRequest.itcode
            else:
                operator = current_itcode.get()
            if operator is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="操作人ITCode不能为空"
                )
            return self.controller.delete_ai_prompt(delete_request.prompt_id, operator)

        @router.post("/upload-jira",
                     summary="上传选定用户故事到jira",
                     description="上传itcode选定的用户故事到jira里")
        def upload_jira( #TODO: 网络调用统一改成httpx以支持异步而非同步忙等
                upload_request:UploadToJiraRequest,
                request: Request
        ):
            """上传用户故事"""
            return self.controller.upload_to_jira(upload_request.story_ids,upload_request.project_key,upload_request.jira_token)

        @router.post("/update",
                     summary="更新用户编辑的用户故事",
                     description="把用户编辑好的用户故事上传到数据库")
        def update_user_story(
                update_request: UpdateUserStroyRequest,
                request: Request
        ):
            # 将请求中的jira字段转换为story_data字典
            story_data = update_request.to_story_data_dict()

            return self.controller.update_user_story(
                uuid=update_request.uuid,
                story_data=story_data
            )

        @router.post("/exhibition",
                     summary="获取用户生成的最新user stroy展示在前端",
                     description="展示user story在前端的卡片上")
        def exhibition_user_story(
                exhibit_request: ExhibitUserStoryRequest,
                request: Request
        ):
            return self.controller.exhibit_user_story(exhibit_request.conversation_id)

        @router.post("/delete",
                     summary="删除选中的用户故事",
                     description="删除uuid对应的用户故事")
        def delete_user_story(
                delete_request: DeleteUserStoryRequest,
                request: Request
        ):
            return self.controller.delete_user_story( delete_request.uuids)

        @router.post("/download",
                     summary="下载选中的用户故事保存为excel文件",
                     description="下载选中的用户故事保存为excel文件")
        def download_user_story(
                download_request: DownloadUserStoryRequest,
                request: Request
        ):
            file_path, file_name = self.controller.download_user_story(
                download_request.uuids
            )

            return FileResponse(
                file_path,
                filename=file_name,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=\"{file_name}\""}
            )
        app.include_router(router)
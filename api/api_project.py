import os

from fastapi import Request, APIRouter, Depends
from config.constants import REQ_ROUTER
from controllers.project_controller import ProjectController
from utils.dependency_injection import get_container
from pydantic import BaseModel, Field

class ProjectListRequest(BaseModel):
    itcode: str = Field(..., description="用户it code")

    class Config:
        json_schema_extra = {
            "example": {
                "itcode": "这是一个itcode"
            }
        }

class GetProjectRequest(BaseModel):
    itcode: str = Field(..., description="用户it code")
    project_id: int = Field(..., description="项目id")

    class Config:
        json_schema_extra = {
            "example": {
                "itcode": "这是一个itcode",
                "project_id": 1
            }
        }

class ApiProject():
    """project API模块"""

    def __init__(self, app):
        self.project_controller = get_container().get_bean(ProjectController)
        self._register_routes(app)

    def _register_routes(self, app):
        """注册所有API路由"""
        req = REQ_ROUTER
        router = APIRouter(
            prefix=req+"/project",
            tags=["Project Management"],
        )

        # @router.post("/list",
        #             summary="获取现有的project（通过itcode）",
        #             description="通过it_code返回project_id")
        # def list_project_id(
        #     project_list_request: ProjectListRequest
        # ):
        #     itcode = project_list_request.itcode
        #     return self.project_controller.get_project_id_by_itcode(itcode=itcode)
        #
        # @router.post("/get",
        #              summary="查看project详情",
        #              description="通过it_code和project_id查询项目详情")
        # def get_project_detail(
        #         get_project_request: GetProjectRequest
        # ):
        #     itcode = get_project_request.itcode
        #     project_id = get_project_request.project_id
        #     return self.project_controller.get_project_detail(itcode=itcode,project_id=project_id)

        app.include_router(router)
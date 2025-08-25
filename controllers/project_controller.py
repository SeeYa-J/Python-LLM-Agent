from services.project_service import ProjectService
from utils.dependency_injection import controller
from utils.response_utils import ApiResponse


@controller
class ProjectController:
    """项目控制器"""
    project_service: ProjectService

    def __init__(self):
        pass

    def get_project_id_by_itcode(self,itcode: str)->dict:
        """获取用户project_id"""
        try:
            projects = self.project_service.query_project_by_creator(itcode) #TODO: 明天换成shuzhen的接口
            result = self.project_service.get_project_id_return_data(projects)
            return ApiResponse.success(result, "用户项目查询成功")
        except Exception as e:
            return ApiResponse.error(f"用户项目查询失败: {str(e)}")

    def get_project_detail(self,project_key: str)->dict:
        """查询项目详情"""
        try:
            project = self.project_service.query_project_by_project_key(project_key)
            result = self.project_service.get_project_return_data(project)
            return ApiResponse.success(result, "用户项目详情获取成功")
        except Exception as e:
            return ApiResponse.error(f"用户项目详情获取失败: {str(e)}")
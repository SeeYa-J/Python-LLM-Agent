# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
"""
Spring风格依赖注入系统演示
展示真正的Spring使用方式：组件注解 + 类型注解属性注入
"""
from services.prompt_service import PromptService
from dao.ai_prompt_dao import AiSystemPromptDAO
from dao.project_dao import BizJiraProjectDAO
from utils.dependency_injection import controller, service
from utils.response_utils import ApiResponse


# 演示1: 复合业务控制器
@controller
class BusinessIntegrationController:
    """业务集成控制器 - 演示多Service注入"""
    # 类型注解定义为类变量，而不是在__init__方法中
    user_story_service: PromptService

    def __init__(self):
        pass

    def create_complete_project(self, project_data: dict, initial_prompts: list, operator: str) -> dict:
        """创建完整项目（包含初始提示词）"""
        try:
            # 直接使用UserStoryService处理项目和提示词
            # 获取项目DAO来创建项目
            project = self.user_story_service.create_project(project_data, operator)

            # 使用用户故事服务创建初始提示词
            created_prompts = []
            for prompt_data in initial_prompts:
                prompt_data['project_id'] = project.id
                prompt = self.user_story_service.create_ai_prompt(prompt_data, operator)
                created_prompts.append(prompt)

            return ApiResponse.success({
                "project": project,
                "initial_prompts": created_prompts,
                "summary": f"成功创建项目 {project.project_name}，包含 {len(created_prompts)} 个初始提示词"
            }, "项目创建完成")

        except Exception as e:
            return ApiResponse.error(f"项目创建失败: {str(e)}")


# 演示2: 跨层级注入（Service中注入DAO，Controller中注入Service）
@service
class AdvancedAnalyticsService:
    """高级分析服务 - 演示直接注入DAO进行复杂查询"""
    # 类型注解定义为类变量
    ai_prompt_dao: AiSystemPromptDAO
    project_dao: BizJiraProjectDAO

    def __init__(self):
        pass

    def get_detailed_analytics(self) -> dict:
        """获取详细分析数据 - 直接使用DAO提高性能"""
        try:
            # 直接使用DAO进行数据查询
            all_prompts = self.ai_prompt_dao.list_all()
            predefined_prompts = self.ai_prompt_dao.find_predefined_prompts()
            all_projects = self.project_dao.list_all()

            analytics = {
                "total_prompts": len(all_prompts),
                "predefined_prompts": len(predefined_prompts),
                "custom_prompts": len(all_prompts) - len(predefined_prompts),
                "total_projects": len(all_projects),
                "prompts_per_project": len(all_prompts) / max(len(all_projects), 1)
            }

            return analytics

        except Exception as e:
            raise Exception(f"分析数据获取失败: {str(e)}")


@controller
class AnalyticsController:
    """分析控制器 - 注入自定义分析服务"""
    # 类型注解定义为类变量
    analytics_service: AdvancedAnalyticsService

    def __init__(self):
        pass

    def get_dashboard_analytics(self) -> dict:
        """获取仪表板分析数据"""
        try:
            analytics = self.analytics_service.get_detailed_analytics()
            return ApiResponse.success(analytics, "分析数据获取成功")

        except Exception as e:
            return ApiResponse.error(f"获取分析数据失败: {str(e)}")


# 演示3: 混合注入模式
@controller
class FlexibleController:
    """灵活控制器 - 演示混合注入模式"""
    # 类型注解定义为类变量
    user_story_service: PromptService  # 注入Service进行业务逻辑处理
    ai_prompt_dao: AiSystemPromptDAO      # 也可以直接注入DAO进行快速数据访问

    def __init__(self):
        pass

    def quick_prompt_check(self, prompt_id: int) -> dict:
        """快速提示词检查 - 直接使用DAO"""
        try:
            # 直接使用DAO进行快速查询
            prompt = self.ai_prompt_dao.get_by_id(prompt_id)
            if not prompt:
                return ApiResponse.error("提示词不存在")

            return ApiResponse.success({
                "id": prompt.id,
                "exists": True,
                "is_predefined": prompt.is_predefined
            })

        except Exception as e:
            return ApiResponse.error(f"检查失败: {str(e)}")

    def business_prompt_operation(self, prompt_data: dict, operator: str) -> dict:
        """业务提示词操作 - 使用Service处理复杂逻辑"""
        try:
            # 使用Service进行业务逻辑处理
            prompt = self.user_story_service.create_ai_prompt(prompt_data, operator)
            return ApiResponse.success(prompt, "提示词创建成功")

        except Exception as e:
            return ApiResponse.error(f"创建失败: {str(e)}")


# 演示如何使用容器获取Bean
def demo_container_usage():
    """演示如何手动从容器获取Bean"""
    from utils.dependency_injection import get_container, setup_dependency_injection

    # 初始化容器，使用None作为mock数据库引擎
    setup_dependency_injection(None)

    container = get_container()

    # 从容器获取Service实例
    user_story_service = container.get_bean(PromptService)

    # 从容器获取Controller实例
    controller = container.get_bean(BusinessIntegrationController)

    print("容器中的组件:")
    print(f"UserStoryService: {user_story_service}")
    print(f"BusinessIntegrationController: {controller}")

    # 验证注入是否成功
    print(f"Controller中的user_story_service: {controller.user_story_service}")
    print(f"是否为同一实例: {user_story_service is controller.user_story_service}")


if __name__ == "__main__":
    # 演示容器使用
    demo_container_usage()

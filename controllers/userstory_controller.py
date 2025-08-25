# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
from typing import List, Optional, Any ,AnyStr

from services.jira_service import JiraService
from services.prompt_service import PromptService
from services.user_story_service import UserStoryService
from utils.response_utils import ApiResponse
from utils.dependency_injection import controller


@controller
class UserStoryController:
    """用户故事控制器"""
    user_story_service: PromptService
    jira_service: JiraService
    story_service: UserStoryService

    def __init__(self):
        pass

    def create_ai_prompt(self, prompt_request: dict, operator: str) -> dict:
        """创建AI系统提示词"""
        try:
            prompt = self.user_story_service.create_ai_prompt(prompt_request, operator)
            return ApiResponse.success(prompt, "AI提示词创建成功")
        except Exception as e:
            return ApiResponse.error(f"创建失败: {str(e)}")

    def get_ai_prompt(self, prompt_id: int) -> dict:
        """获取AI系统提示词详情"""
        prompt = self.user_story_service.get_ai_prompt_by_id(prompt_id)
        if not prompt:
            return ApiResponse.error("提示词不存在")

        return ApiResponse.success(prompt)

    def list_prompts_by_jira_project(self, project_key: str, is_predefined: Optional[bool] = None) -> dict:
        """根据项目ID, 是否预定义，获取提示词列表"""

        prompts = {"prompts" : self.user_story_service.get_prompts_titles_by_jira_project_and_predefined(project_key, is_predefined)}
        return ApiResponse.success(prompts)

    def list_predefined_prompts(self) -> dict:
        """获取预制提示词列表"""
        prompts = self.user_story_service.get_predefined_prompts()
        return ApiResponse.list_success(prompts)

    def update_ai_prompt(self, prompt_id: int, prompt_request: dict, operator: str) -> dict:
        """更新AI系统提示词"""
        try:
            updated_prompt = self.user_story_service.update_ai_prompt(prompt_id, prompt_request, operator)
            if not updated_prompt:
                return ApiResponse.error("提示词不存在")

            return ApiResponse.success(updated_prompt, "更新成功")
        except Exception as e:
            return ApiResponse.error(f"更新失败: {str(e)}")

    def delete_ai_prompt(self, prompt_id: int, operator: str) -> dict:
        """删除AI系统提示词"""
        try:
            success = self.user_story_service.delete_ai_prompt(prompt_id, operator)
            if success:
                return ApiResponse.success(message="删除成功")
            else:
                return ApiResponse.error("提示词不存在")
        except Exception as e:
            return ApiResponse.error(f"删除失败: {str(e)}")

    def upload_to_jira(self, itcode: str,story_ids: list[int], project_key: str,jira_token: str) -> dict:
        """上传用户故事"""
        try:
            # 调用服务层方法
            # result = self.jira_service.upload_stories_to_jira(itcode, story_ids, project_id=jira_project_id) # TODO：测试无误就删掉这个方法及其子方法
            result = self.jira_service.upload_stories_to_jira_by_api(itcode, story_ids, project_key,jira_token)

            # 根据返回结果判断成功或失败
            if result['success']:
                return ApiResponse.success(
                    message=result['message'],
                    data={
                        'results': result['results'],
                        'total_count': result['total_count'],
                        'success_count': result['success_count']
                    }
                )
            else:
                return ApiResponse.error(result['message'])


        except Exception as e:
            return ApiResponse.error(f"未知错误: {str(e)}")


    def update_user_story(self,itcode: str,uuid: str,story_data: dict[str, Any],operator: str) -> dict:
        """更新用户故事"""
        try:
            success = self.story_service.update_user_story(itcode, uuid,story_data,operator)
            if not success:
                return ApiResponse.error("用户故事不存在")

            return ApiResponse.success(success, "更新成功")
        except Exception as e:
            return ApiResponse.error(f"更新失败: {str(e)}")

    def exhibit_user_story(self,itcode: str,conversation_id:int ,operator: str) -> dict:
        """展示用户故事"""
        try:
            success = self.story_service.exhibit_user_story(itcode,conversation_id,operator)
            if not isinstance(success, int):
                return ApiResponse.list_success(success)
            elif success==1 :
                return ApiResponse.error("itcode错误")
        except Exception as e:
            return ApiResponse.error(f"展示失败: {str(e)}")

    def delete_user_story(self,itcode: str,uuids:list[str] ,operator: str) -> dict:
        """批量删除选中的用户故事"""
        try:
            success = self.story_service.batch_delete_selected_stories(itcode,uuids,operator)
            if success:
                return ApiResponse.success(message = f"删除成功{success}条故事")
            else:
                return ApiResponse.error("itcode错误 或 用户故事已被删除")

        except Exception as e:
            return ApiResponse.error(f"删除失败原因: {str(e)}")

    def download_user_story(self, itcode: str, uuids: list[str], operator: str) -> tuple[str, str]:
        """下载用户故事，返回文件路径和文件名"""
        return self.story_service.export_to_excel(itcode, uuids)
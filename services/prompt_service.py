# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
from typing import List, Optional, Any, Dict
from config_service import ConfigService
from models.business_entities import AiSystemPrompt, BizJiraProject, BizDomain
from dao.ai_prompt_dao import AiSystemPromptDAO
from dao.project_dao import BizJiraProjectDAO
from dao.domain_dao import BizDomainDAO
from utils.dependency_injection import service
import os


@service
class PromptService:
    """处理prompt的服务层"""
    ai_prompt_dao: AiSystemPromptDAO
    project_dao: BizJiraProjectDAO
    domain_dao: BizDomainDAO
    config_service: ConfigService

    def __init__(self):
        pass

    # AI系统提示词相关服务方法
    def create_ai_prompt(self, prompt_data: dict) -> AiSystemPrompt:
        """创建AI系统提示词"""
        prompt = AiSystemPrompt(**prompt_data)
        return self.ai_prompt_dao.create(prompt)

    def get_ai_prompt_by_id(self, prompt_id: int) -> Dict[str, Any]:
        """根据ID获取AI系统提示词"""
        return self.ai_prompt_dao.find_by_prompt_id(prompt_id)
    
    def get_prompts_titles_by_itcode_and_predefined(self, itcode: str, is_predefined: Optional[bool] = None) -> List[dict[str, Any]]:
        """根据itcode获取提示词列表"""
        return self.ai_prompt_dao.find_titles_by_itcode_and_predefined(itcode, is_predefined)

    def get_prompts_by_domain(self, domain_id: int) -> List[AiSystemPrompt]:
        """根据域ID获取提示词列表"""
        return self.ai_prompt_dao.find_by_domain_id(domain_id)

    def get_predefined_prompts(self) -> List[AiSystemPrompt]:
        """获取预制提示词列表"""
        return self.ai_prompt_dao.find_predefined_prompts()

    def update_ai_prompt(self, prompt_id: int, prompt_data: dict) -> Optional[AiSystemPrompt]:
        """更新AI系统提示词"""
        existing_prompt = self.ai_prompt_dao.get_by_id(prompt_id)# 先查询是否存在当前要修改的提示词id
        if not existing_prompt:
            return None

        # 更新字段
        for key, value in prompt_data.items():
            if hasattr(existing_prompt, key):
                setattr(existing_prompt, key, value)

        return self.ai_prompt_dao.update(existing_prompt)

    def delete_ai_prompt(self, prompt_id: int) -> bool:
        """删除AI系统提示词"""
        return self.ai_prompt_dao.soft_delete(prompt_id)

    # 项目相关服务方法
    def create_project(self, project_data: dict) -> BizJiraProject:
        """创建项目"""
        project = BizJiraProject(**project_data)
        return self.project_dao.create(project)

    def get_project_by_id(self, project_id: int) -> Optional[BizJiraProject]:
        """根据ID获取项目"""
        return self.project_dao.get_by_id(project_id)

    def get_project_by_key(self, project_key: str) -> Optional[BizJiraProject]:
        """根据项目标识获取项目"""
        return self.project_dao.find_by_project_key(project_key)

    def list_projects(self, page: int = 1, size: int = 20) -> List[BizJiraProject]:
        """分页获取项目列表"""
        return self.project_dao.list_all(page, size)

    # 域相关服务方法
    def create_domain(self, domain_data: dict) -> BizDomain:
        """创建域"""
        domain = BizDomain(**domain_data)
        return self.domain_dao.create(domain)

    def get_domain_by_id(self, domain_id: int) -> Optional[BizDomain]:
        """根据ID获取域"""
        return self.domain_dao.get_by_id(domain_id)

    def get_domain_by_code(self, domain_code: str) -> Optional[BizDomain]:
        """根据域编码获取域"""
        return self.domain_dao.find_by_domain_code(domain_code)

    def list_domains(self, page: int = 1, size: int = 20) -> List[BizDomain]:
        """分页获取域列表"""
        return self.domain_dao.list_all(page, size)


    def get_summary_prompt(self,user_input):
        """获取总结用户提问提示词并且插入用户输入"""

        summary_prompt =self.config_service.data["prompt_id"]["summary_prompt_id"]
        summary_prompt = summary_prompt.format(user_input=user_input)
        return summary_prompt



    def get_user_story_summary_prompt(self,user_story_str: str)->str:
        """获取用户故事总结提示词"""

        user_story_summary_prompt = self.config_service.data["prompt_id"]["user_story_summary_prompt_id"]
        user_story_summary_prompt = user_story_summary_prompt.format(user_input=user_story_str)
        return user_story_summary_prompt




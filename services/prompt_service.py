# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
from typing import List, Optional, Any, Dict
from config_service import ConfigService
from models.business_entities import AiSystemPrompt, BizJiraProject, BizDomain
from dao.ai_prompt_dao import AiSystemPromptDAO
from dao.project_dao import BizJiraProjectDAO
from dao.domain_dao import BizDomainDAO
from utils.dependency_injection import service
import os

'''

根据对应id获取 对应Prompt，并插入userInput
'''

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
    def create_ai_prompt(self, prompt_data: dict, operator: str) -> AiSystemPrompt:
        """创建AI系统提示词"""
        prompt = AiSystemPrompt(**prompt_data)
        return self.ai_prompt_dao.create(prompt, operator)

    def get_ai_prompt_by_id(self, prompt_id: int) -> Dict[str, Any]:
        """根据ID获取AI系统提示词"""
        return self.ai_prompt_dao.find_by_prompt_id(prompt_id)

    def get_prompts_titles_by_jira_project_and_predefined(self, project_key: str, is_predefined: Optional[bool] = None) -> List[dict[str, Any]]:
        """根据项目ID获取提示词列表"""
        return self.ai_prompt_dao.find_titles_by_jira_project_key_and_predefined(project_key, is_predefined)

    def get_prompts_by_domain(self, domain_id: int) -> List[AiSystemPrompt]:
        """根据域ID获取提示词列表"""
        return self.ai_prompt_dao.find_by_domain_id(domain_id)

    def get_predefined_prompts(self) -> List[AiSystemPrompt]:
        """获取预制提示词列表"""
        return self.ai_prompt_dao.find_predefined_prompts()

    def update_ai_prompt(self, prompt_id: int, prompt_data: dict, operator: str) -> Optional[AiSystemPrompt]:
        """更新AI系统提示词"""
        existing_prompt = self.ai_prompt_dao.get_by_id(prompt_id)# 先查询是否存在当前要修改的提示词id
        if not existing_prompt:
            return None

        # 更新字段
        for key, value in prompt_data.items():
            if hasattr(existing_prompt, key):
                setattr(existing_prompt, key, value)

        return self.ai_prompt_dao.update(existing_prompt, operator)

    def delete_ai_prompt(self, prompt_id: int, operator: str) -> bool:
        """删除AI系统提示词"""
        return self.ai_prompt_dao.soft_delete(prompt_id, operator)

    # 项目相关服务方法
    def create_project(self, project_data: dict, operator: str) -> BizJiraProject:
        """创建项目"""
        project = BizJiraProject(**project_data)
        return self.project_dao.create(project, operator)

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
    def create_domain(self, domain_data: dict, operator: str) -> BizDomain:
        """创建域"""
        domain = BizDomain(**domain_data)
        return self.domain_dao.create(domain, operator)

    def get_domain_by_id(self, domain_id: int) -> Optional[BizDomain]:
        """根据ID获取域"""
        return self.domain_dao.get_by_id(domain_id)

    def get_domain_by_code(self, domain_code: str) -> Optional[BizDomain]:
        """根据域编码获取域"""
        return self.domain_dao.find_by_domain_code(domain_code)

    def list_domains(self, page: int = 1, size: int = 20) -> List[BizDomain]:
        """分页获取域列表"""
        return self.domain_dao.list_all(page, size)

    def get_judge_user_scenarios_prompt(self,user_input:str):
        """获取判断用户应用场景提示词 并且插入用户输入"""
        # self.config_service.data==所有相关yaml（配置）
        judge_user_scenarios_prompt_id = self.config_service.data["prompt_id"]["judge_user_scenarios_prompt_id"]
        # SQLModel 根据 id查找表
        judge_user_scenarios_prompt_info = self.ai_prompt_dao.get_by_id(judge_user_scenarios_prompt_id)
        judge_user_scenarios_prompt = judge_user_scenarios_prompt_info.content #获取该用户提示词内容str
        judge_user_scenarios_prompt = judge_user_scenarios_prompt.format(user_input=user_input)# 'str{user_input}'.format
        return judge_user_scenarios_prompt

    def get_summary_prompt(self,user_input):
        """从数据库 获取总结用户提问提示词（id 9，在dev.yaml）并且插入用户输入"""
        summary_prompt_id = self.config_service.data["prompt_id"]["summary_prompt_id"]
        summary_prompt_info = self.ai_prompt_dao.get_by_id(summary_prompt_id)
        summary_prompt = summary_prompt_info.content
        summary_prompt = summary_prompt.format(user_input=user_input)
        return summary_prompt

    def get_system_prompt(self,user_input: str,document_context: str)->str:
        """获取系统提示词  并且插入用户输入"""
        system_prompt_id = self.config_service.data["prompt_id"]["system_prompt_id"]
        system_prompt_info = self.ai_prompt_dao.get_by_id(system_prompt_id)
        system_prompt = system_prompt_info.content
        system_prompt = system_prompt.format(user_input=user_input,user_context=document_context)
        return system_prompt

    def get_user_story_summary_prompt(self,user_story_str: str)->str:
        """获取用户故事总结提示词  并且插入用户输入"""
        user_story_summary_prompt_id = self.config_service.data["prompt_id"]["user_story_summary_prompt_id"]
        user_story_summary_prompt_info = self.ai_prompt_dao.get_by_id(user_story_summary_prompt_id)
        user_story_summary_prompt = user_story_summary_prompt_info.content
        user_story_summary_prompt = user_story_summary_prompt.format(user_input=user_story_str)
        return user_story_summary_prompt

    def get_create_user_story_prompt(self, user_input: str,knowledge: str,document:str) -> str:
        """获取生成用户故事提示词  并且插入用户输入"""
        divide_user_story_prompt_id = self.config_service.data["prompt_id"]["divide_user_story_prompt_id"]
        divide_user_story_prompt_info = self.ai_prompt_dao.get_by_id(divide_user_story_prompt_id)
        divide_user_story_prompt = divide_user_story_prompt_info.content
        divide_user_story_prompt = divide_user_story_prompt.format(user_input=user_input
                                                                   ,knowledge=knowledge
                                                                   ,document=document)
        return divide_user_story_prompt

    def get_update_user_story_prompt(self, user_input: str, original_scheme: str) -> str:
        """获取修改用户故事提示词  并且插入用户输入"""
        divide_user_story_prompt_id = self.config_service.data["prompt_id"]["update_user_story_prompt_id"]
        divide_user_story_prompt_info = self.ai_prompt_dao.get_by_id(divide_user_story_prompt_id)
        divide_user_story_prompt = divide_user_story_prompt_info.content
        divide_user_story_prompt = divide_user_story_prompt.format(user_input=user_input,
                                                            original_scheme=original_scheme)
        return divide_user_story_prompt

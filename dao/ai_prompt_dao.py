# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
from typing import List, Optional, Any, Dict
from sqlmodel import Session, select, col
from dao.base_dao import BaseDAO
from models.business_entities import AiSystemPrompt
from utils.dependency_injection import repository


@repository
class AiSystemPromptDAO(BaseDAO[AiSystemPrompt]):
    """AI系统提示词DAO"""

    def __init__(self, db_engine):
        super().__init__(db_engine, AiSystemPrompt)
        
    def find_by_jira_project_key_and_predefined(self, project_key: str, is_predefined: Optional[bool] = None) -> List[AiSystemPrompt]:
        """根据JIRA项目key和是否预定义查询提示词"""
        with Session(self.db_engine) as session:
            statement = select(AiSystemPrompt).where(
                AiSystemPrompt.project_key == project_key,
                AiSystemPrompt.is_deleted == False
            )
            if is_predefined is not None:
                statement = statement.where(AiSystemPrompt.is_predefined == is_predefined)
            return list(session.exec(statement).all())

    def find_titles_by_jira_project_key_and_predefined(self, project_key: str, is_predefined: Optional[bool] = None) -> List[dict[str, Any]]:
        """根据JIRA项目Key和是否预定义查询提示词标题"""
        with Session(self.db_engine) as session:
            statement = select(AiSystemPrompt.id, AiSystemPrompt.title, AiSystemPrompt.is_predefined).where(
                AiSystemPrompt.project_key == project_key,
                AiSystemPrompt.is_deleted == False
            )
            if is_predefined is not None:
                statement = statement.where(AiSystemPrompt.is_predefined == is_predefined)
            
            results = session.exec(statement).all()
            return [
                {
                    "id": row[0],
                    "title": row[1], 
                    "is_predefined": row[2]
                }
                for row in results
            ]
        
    def find_by_prompt_id(self, prompt_id: int) -> Dict[str, Any]:
        """根据提示词ID查询提示词"""
        with Session(self.db_engine) as session:
            statement = select(AiSystemPrompt).where(
                AiSystemPrompt.id == prompt_id,
                AiSystemPrompt.is_deleted == False,
            )
            result = session.exec(statement).first()
            if result:
                return {
                    "id": result.id,
                    "title": result.title,
                    "content": result.content,
                    "is_predefined": result.is_predefined,
                    "description": result.description,
                    "project_key": result.project_key,
                    "domain_id": result.domain_id,
                }
            return {}

    def find_by_domain_id(self, domain_id: int) -> List[AiSystemPrompt]:
        """根据域ID查询提示词"""
        with Session(self.db_engine) as session:
            statement = select(AiSystemPrompt).where(
                AiSystemPrompt.domain_id == domain_id,
                AiSystemPrompt.is_deleted == False
            )
            return list(session.exec(statement).all())

    def find_predefined_prompts(self) -> List[AiSystemPrompt]:
        """查询预制提示词"""
        with Session(self.db_engine) as session:
            statement = select(AiSystemPrompt).where(
                AiSystemPrompt.is_predefined == True,
                AiSystemPrompt.is_deleted == False
            )
            return list(session.exec(statement).all())

    def find_by_id(self, id: int) -> Optional[AiSystemPrompt]:
        """根据id查询项目提示词"""
        with Session(self.db_engine) as session:
            statement = select(AiSystemPrompt).where(
                AiSystemPrompt.id == id,
                AiSystemPrompt.is_deleted == False
            )
            return list(session.exec(statement))

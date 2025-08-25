# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
from typing import List, Optional
from sqlmodel import Session, select
from dao.base_dao import BaseDAO
from models.business_entities import BizJiraProject
from utils.dependency_injection import repository


@repository
class BizJiraProjectDAO(BaseDAO[BizJiraProject]):
    """业务JIRA项目DAO - 通用项目数据访问层"""

    def __init__(self, db_engine):
        super().__init__(db_engine, BizJiraProject)

    def find_by_project_key(self, project_key: str) -> Optional[BizJiraProject]:
        """根据项目标识查询项目"""
        with Session(self.db_engine) as session:
            statement = select(BizJiraProject).where(
                BizJiraProject.project_key == project_key,
                BizJiraProject.is_deleted == False
            )
            return session.exec(statement).first()

    def find_by_project_id(self, project_id: int) -> BizJiraProject | str | None:
        """根据项目id查询项目"""
        with Session(self.db_engine) as session:
            statement = select(BizJiraProject.project_key).where(
                BizJiraProject.id == project_id,
                BizJiraProject.is_deleted == False
            )
            return session.exec(statement).first()

    def find_by_creator(self,creator: str)->List[BizJiraProject]:
        """根据creator查询project"""
        with Session(self.db_engine) as session:
            statement = select(BizJiraProject).where(
                BizJiraProject.create_by == creator,
                BizJiraProject.is_deleted == False
            )
            return list(session.exec(statement).all())

    def find_by_project_id_and_creator(self,creator: str,project_id: int)->BizJiraProject:
        """根据creator以及project_id查询project"""
        with Session(self.db_engine) as session:
            statement = select(BizJiraProject).where(
                BizJiraProject.id == project_id,
                BizJiraProject.create_by == creator,
                BizJiraProject.is_deleted == False
            )
            return session.exec(statement).first()

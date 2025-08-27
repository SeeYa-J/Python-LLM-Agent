# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
# dao/biz_user_dao.py
from typing import Optional
from sqlmodel import Session, select
from dao.base_dao import BaseDAO
from models.business_entities import BizUser
from utils.dependency_injection import repository
from datetime import datetime
from config.context import current_itcode

@repository
class BizUserDAO(BaseDAO[BizUser]):
    """用户 DAO"""

    def __init__(self, db_engine):
        super().__init__(db_engine, BizUser)

    # def find_jira_token_by_id(self, user_id: int) -> Optional[str]:
    #     """
    #     根据用户ID查询JIRA Token
    #     """
    #     with Session(self.db_engine) as session:
    #         stmt = (
    #             select(BizUser.jira_token)
    #             .where(
    #                 BizUser.id == user_id,
    #                 BizUser.is_deleted == False
    #             )
    #         )
    #         result = session.exec(stmt).first()
    #         return result

    def find_jira_token_by_itcode(self) -> Optional[str]:
        """
        根据用户ITCODE查询JIRA Token
        """
        with Session(self.db_engine) as session:
            stmt = (
                select(BizUser.jira_token)
                .where(
                    BizUser.itcode == current_itcode.get(),
                    BizUser.is_deleted == False
                )
            )
            result = session.exec(stmt).first()
            return result

    # def find_by_itcode(self) -> Optional[BizUser]:
    #     """
    #     根据用户IT代码查询用户信息
    #     """
    #     with Session(self.db_engine) as session:
    #         stmt = (
    #             select(BizUser)
    #             .where(
    #                 BizUser.itcode == current_itcode.get(),
    #                 BizUser.is_deleted == False
    #             )
    #         )
    #         return session.exec(stmt).first()

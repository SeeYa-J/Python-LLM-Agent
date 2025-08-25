# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
from typing import Optional
from sqlmodel import Session, select
from dao.base_dao import BaseDAO
from models.business_entities import BizDomain
from utils.dependency_injection import repository


@repository
class BizDomainDAO(BaseDAO[BizDomain]):
    """业务域DAO - 通用域数据访问层"""

    def __init__(self, db_engine):
        super().__init__(db_engine, BizDomain)

    def find_by_domain_code(self, domain_code: str) -> Optional[BizDomain]:
        """根据域编码查询域"""
        with Session(self.db_engine) as session:
            statement = select(BizDomain).where(
                BizDomain.domain_code == domain_code,
                BizDomain.is_deleted == False
            )
            return session.exec(statement).first()

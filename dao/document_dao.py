# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
from typing import Optional
from sqlmodel import Session, select
from dao.base_dao import BaseDAO
from models.business_entities import AiUploadDocument
from utils.dependency_injection import repository
from datetime import datetime

@repository
class AiUploadDocumentDAO(BaseDAO[AiUploadDocument]):
    # 表示 AiUploadDocumentDAO类继承自 BaseDAO类
    # 泛型参数为AiUploadDocument即DAO 处理的实体类型。
    """用户上传文件DAO"""

    def __init__(self, db_engine):
        super().__init__(db_engine, AiUploadDocument)

    def set_conversation_id(self, id: int, conversation_id: int,operator: str) -> bool:
        """设置conversation_id"""
        with Session(self.db_engine) as session:
            entity = session.get(self.model_class, id)
            if entity:
                entity.conversation_id = conversation_id
                entity.modify_by = operator
                entity.modify_time = datetime.now()
                session.add(entity)
                session.commit()
                return True
            return False
# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
from abc import ABC
from datetime import datetime
from typing import TypeVar, Generic, List, Optional
from sqlmodel import Session, select
from config.constants import UTC8ZOME
from models.base_entity import BaseEntity
from config.context import current_itcode

T = TypeVar('T', bound=BaseEntity)


class BaseDAO(Generic[T], ABC):
    """
    基础DAO类，提供通用的数据库操作方法
    """

    def __init__(self, db_engine, model_class: type[T]):
        self.db_engine = db_engine
        self.model_class = model_class

    def create(self, entity: T) -> T:
        """创建记录"""
        entity.create_by = current_itcode.get()
        entity.modify_by = current_itcode.get()

        with Session(self.db_engine) as session:
            session.add(entity)
            session.commit()
            session.refresh(entity)
            return entity

    def get_by_id(self, entity_id: int) -> Optional[T]:
        """根据ID获取记录"""
        with Session(self.db_engine) as session:
            statement = select(self.model_class).where(
                self.model_class.id == entity_id,
                self.model_class.is_deleted == False
            )
            return session.exec(statement).first()

    def list_all(self, page: int = 1, size: int = 20) -> List[T]:
        """分页查询所有记录"""
        with Session(self.db_engine) as session:
            statement = select(self.model_class).where(
                self.model_class.is_deleted == False
            ).offset((page - 1) * size).limit(size)
            return list(session.exec(statement).all())

    def update(self, entity: T) -> T:
        """更新记录"""
        entity.modify_by = current_itcode.get()
        entity.modify_time = datetime.now(tz=UTC8ZOME)

        with Session(self.db_engine) as session:
            session.add(entity)
            session.commit()
            session.refresh(entity)
            return entity

    def soft_delete(self, entity_id: int) -> bool:
        """软删除记录"""
        with Session(self.db_engine) as session:
            entity = session.get(self.model_class, entity_id)
            if entity:
                entity.is_deleted = True
                entity.modify_by = current_itcode.get()
                entity.modify_time = datetime.now(tz=UTC8ZOME)
                session.add(entity)
                session.commit()
                return True
            return False

    def count(self) -> int:
        """统计记录数量"""
        with Session(self.db_engine) as session:
            statement = select(self.model_class).where(
                self.model_class.is_deleted == False
            )
            return len(list(session.exec(statement).all()))

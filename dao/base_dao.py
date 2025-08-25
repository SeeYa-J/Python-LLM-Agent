# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
from abc import ABC
from datetime import datetime
from typing import TypeVar, Generic, List, Optional
from sqlmodel import Session, select
from config.constants import UTC8ZOME
from models.base_entity import BaseEntity
from config.context import current_itcode

T = TypeVar('T', bound=BaseEntity) #定义一个基础实体类，包含所有表的公共字段（类似主键）
'''BaseEntity: 创建时间、修改时间、创建者、修改者、是否删除'''

class BaseDAO(Generic[T], ABC):
    """
    基础DAO类，提供通用的数据库操作方法
    """

    def __init__(self, db_engine, model_class: type[T]):
        self.db_engine = db_engine  # SQLAlchemy 引擎 链接各种数据库
        self.model_class = model_class  # 实体类#即表

    def create(self, entity: T, operator: str) -> T:
        """创建记录，需写入："""
        entity.create_by = current_itcode.get() # 填充当前操作人itcode
        entity.modify_by = current_itcode.get()

        with Session(self.db_engine) as session: # 创建会话
            session.add(entity) # 添加数据
            session.commit() # 提交数据
            session.refresh(entity) #刷新
            return entity # 返回创建对象

    def get_by_id(self, entity_id: int) -> Optional[T]:
        """根据ID获取记录"""
        with Session(self.db_engine) as session:
            statement = select(self.model_class).where( #查询
                self.model_class.id == entity_id,
                self.model_class.is_deleted == False
            )
            return session.exec(statement).first()# exec执行查询并返回first记录

    def list_all(self, page: int = 1, size: int = 20) -> List[T]:
        """分页查询所有记录,这里就是一次性 查 （page-1）*size ~ page*size 记录"""
        with Session(self.db_engine) as session:
            statement = select(self.model_class).where(
                self.model_class.is_deleted == False
            ).offset((page - 1) * size).limit(size) # limit（size）限制返回size条记录
            # offset表示跳过前面的多少条记录，如果每页显示20条，第一页：跳过0条（即从第1条开始），第二页跳过20条
            return list(session.exec(statement).all()) #[ model_class_1（列名1=value...),...]

    def update(self, entity: T, operator: str) -> T:
        """更新记录"""
        entity.modify_by = current_itcode.get() # 操作人itcode
        entity.modify_time = datetime.now(tz=UTC8ZOME) # 获取当前修改时间

        with Session(self.db_engine) as session:
            session.add(entity)
            session.commit()
            session.refresh(entity)
            return entity

    def soft_delete(self, entity_id: int, operator: str) -> bool:
        """软删除记录"""
        with Session(self.db_engine) as session:
            entity = session.get(self.model_class, entity_id) # get，主键快捷查询
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

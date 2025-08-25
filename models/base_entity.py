# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
from datetime import datetime
from sqlmodel import SQLModel, Field
from config.constants import UTC8ZOME


class BaseEntity(SQLModel):
    """
    基础实体类，包含所有表的公共字段
    """
    create_time: datetime = Field(default_factory=lambda: datetime.now(tz=UTC8ZOME), description="记录创建时间")
    modify_time: datetime = Field(default_factory=lambda: datetime.now(tz=UTC8ZOME), description="记录更新时间")
    create_by: str = Field(max_length=50, description="创建者itcode")
    modify_by: str = Field(max_length=50, description="最后更新者itcode")
    is_deleted: bool = Field(default=False, description="0-未删除，1-已删除")

    class Config:
        from_attributes = True  # from_attributes = True 让你的 SQLModel 类能够从任何具有相应属性的对象（特别是数据库查询结果）创建实例，这是现代 Python API 开发中的标准配置。


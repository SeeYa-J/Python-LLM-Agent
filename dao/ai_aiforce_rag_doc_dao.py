from typing import Optional
from sqlmodel import Session, select

from config.context import current_itcode
from dao.base_dao import BaseDAO
from models.business_entities import AiAiforceRagDoc
from utils.dependency_injection import repository
from datetime import datetime

@repository
class AiAiforceRagDocDAO(BaseDAO[AiAiforceRagDoc]):
    """rag结果DAO"""

    def __init__(self, db_engine):
        super().__init__(db_engine, AiAiforceRagDoc)
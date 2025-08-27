from typing import List, Optional
from sqlmodel import Session, select, desc
from config.context import current_itcode
from dao.base_dao import BaseDAO
from models.business_entities import AiChatSession, AiChatSessionDetail
from utils.dependency_injection import repository


@repository
class AiChatSessionDAO(BaseDAO[AiChatSession]):
    """AI会话DAO"""

    def __init__(self, db_engine):
        super().__init__(db_engine, AiChatSession)

    def query_chat_by_session_id(self,session_id: str)->Optional[AiChatSession]:
        """根据session_id查询历史会话"""
        with Session(self.db_engine) as session:
            statement = select(AiChatSession).where(
                AiChatSession.session_id == session_id,
                AiChatSession.is_deleted == False
            )
            return session.exec(statement).first()

    def query_chat_by_creator_and_project_key(self,project_key: str)->List[AiChatSession]:
        """根据creator以及project_key查询历史会话"""
        with Session(self.db_engine) as session:
            statement = select(AiChatSession).where(
                AiChatSession.create_by == current_itcode.get(),
                AiChatSession.project_key == project_key,
                AiChatSession.is_deleted == False
            )\
            .order_by(desc(AiChatSession.id))  # 按照id降序排序
            return list(session.exec(statement).all())
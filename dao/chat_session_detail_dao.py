from typing import List, Optional
from sqlmodel import Session, select, desc
from dao.base_dao import BaseDAO
from models.business_entities import AiChatSession, AiChatSessionDetail
from utils.dependency_injection import repository


@repository
class AiChatSessionDetailDAO(BaseDAO[AiChatSessionDetail]):
    """AI会话详情DAO"""

    def __init__(self, db_engine):
        super().__init__(db_engine, AiChatSessionDetail)

    def query_chat_detail_by_session_id(self,session_id: str)->List[AiChatSessionDetail]:
        """根据session_id查询会话详情，并且按照round_number降序排列"""
        with Session(self.db_engine) as session:
            statement = select(AiChatSessionDetail).where(
                AiChatSessionDetail.session_id == session_id,
                AiChatSessionDetail.is_deleted == False
            )\
            .order_by(desc(AiChatSessionDetail.round_number))  # 添加降序排序
            return list(session.exec(statement).all())
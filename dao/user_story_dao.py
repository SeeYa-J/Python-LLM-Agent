# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
# dao/biz_user_story_dao.py
from typing import List , Optional,Dict
from sqlmodel import Session, select, func, asc, desc
from sqlalchemy import or_
from dao.base_dao import BaseDAO
from models.business_entities import BizUserStory,BizJiraUploadRecord
from utils.dependency_injection import repository
from datetime import datetime
from config.context import current_itcode

@repository
class BizUserStoryDAO(BaseDAO[BizUserStory]):
    """用户故事 DAO"""

    def __init__(self, db_engine):
        super().__init__(db_engine, BizUserStory)

    def find_for_upload(
            self,
            story_ids: List[int]
    ) -> List[BizUserStory]:
        """
        第二步：根据 story_ids 直接获取完整的用户故事对象
        前面已经过滤了所有条件，这里直接根据ID获取即可
        """
        with Session(self.db_engine) as session:
            stmt = select(BizUserStory).where(BizUserStory.id.in_(story_ids))
            return list(session.exec(stmt).all())

    def find_for_upload1(
            self,
            itcode: str,
            story_ids: List[int]
    ) -> List[BizUserStory]:

        with Session(self.db_engine) as session:
            stmt = select(BizUserStory).join(
                BizJiraUploadRecord, BizUserStory.jira_id == BizJiraUploadRecord.id, isouter=True
            ).where(
                BizUserStory.id.in_(story_ids),
                BizUserStory.is_deleted == False,
                BizUserStory.create_by == current_itcode.get(),
                or_(
                    BizUserStory.jira_id.is_(None),
                    BizJiraUploadRecord.jira_issue_key.is_(None)
                )
            )
            return session.exec(stmt).all()

    def update_jira_id2(self, story_id:int, jira_id:int):
        # 表BizJiraUploadRecord里面根据story_id更新jira_id
        with Session(self.db_engine) as session:
            record = session.get(BizUserStory, story_id)
            if record:
                record.jira_id = jira_id
                session.add(record)
                session.commit()
                return True
            return False


    def update_jira_id(self, itcode: str) -> dict:
        """通过查询上传记录表来更新用户故事的 jira_id"""
        with Session(self.db_engine) as session:
            stmt = (
                select(BizJiraUploadRecord.story_id, BizJiraUploadRecord.id)
                .where(
                    BizJiraUploadRecord.status == '成功',
                    BizJiraUploadRecord.create_by == current_itcode.get(),
                    BizJiraUploadRecord.jira_issue_key.is_not(None)
                )
            )
            success_records = session.exec(stmt).all()

            updated_story_ids = []
            for story_id, id in success_records:
                story = session.get(BizUserStory, story_id)
                if story and story.jira_id is None:
                    story.jira_id = id
                    session.add(story)
                    updated_story_ids.append(story_id)

            session.commit()

            return {
                'success': len(updated_story_ids) > 0,
                'message': f"共更新 {len(updated_story_ids)} 条用户故事的 jira_id。",
                'updated_ids': updated_story_ids
            }

    def find_user_story_by_uuid(self,uuid: str) -> Optional[BizUserStory]:
        """获取该卡片最新的内容"""
        with Session(self.db_engine) as session:
            stmt = (
                select(BizUserStory)
                    .where(
                        BizUserStory.uuid == uuid,
                        BizUserStory.is_deleted == False,
                        BizUserStory.version == -1,
                        )
            )
            return session.exec(stmt).first()

    def get_max_version_by_uuid(self, uuid: str) -> int:
        """获取指定uuid对应的最大版本号"""
        with Session(self.db_engine) as session:
            stmt = (
                select(func.max(BizUserStory.version))
                .where(
                    BizUserStory.uuid == uuid,
                    BizUserStory.is_deleted == False
                )
            )
            result = session.exec(stmt).first()
            return result if result is not None else 0

    def find_user_story_by_conversation_id(self, itcode: str, conversation_id: int) -> List[dict]:
        """
        查询指定会话和用户创建的所有最新版本用户故事
        SQL逻辑：
        select * from biz_user_story
        where uuid in (
            select uuid from biz_user_story bus
            where bus.conversation_id = :conversation_id and create_by = :itcode
        )
        and version = -1
        """
        with Session(self.db_engine) as session:
            # 先查出所有符合条件的uuid
            sub_stmt = (
                select(BizUserStory.uuid)
                .where(
                    BizUserStory.conversation_id == conversation_id,
                    BizUserStory.is_deleted == False,
                    BizUserStory.create_by == current_itcode.get()
                )
                .order_by(asc(BizUserStory.order))
            )
            uuid_list = [row for row in session.exec(sub_stmt).all()]
            if not uuid_list:
                return []

            # 再查出这些uuid且version=-1的用户故事，左连接jira上传记录表
            stmt = (
                select(
                    BizUserStory,
                    BizJiraUploadRecord.jira_issue_key,
                    BizJiraUploadRecord.url
                )
                .outerjoin(BizJiraUploadRecord, BizUserStory.jira_id == BizJiraUploadRecord.id)
                .where(
                    BizUserStory.uuid.in_(uuid_list),
                    BizUserStory.version == -1
                )
                .order_by(asc(BizUserStory.order))
            )

            results = []
            for user_story, jira_issue_key, jira_url in session.exec(stmt).all():
                story_dict = user_story.model_dump()
                story_dict.update({'jira_issue_key': jira_issue_key, 'jira_url': jira_url})
                results.append(story_dict)

            return results

    def find_user_story_by_uuids(self, itcode:str,uuids: List[str]) -> List[BizUserStory]:
        """根据UUID列表查询用户故事（只返回最新版本）"""
        with Session(self.db_engine) as session:
            stmt = (
                select(BizUserStory)
                .where(
                    BizUserStory.uuid.in_(uuids),
                    BizUserStory.create_by == current_itcode.get(),
                    BizUserStory.is_deleted == False,
                    BizUserStory.version == -1  # 只查询最新版本
                )
            )
            return list(session.exec(stmt).all())

    def query_user_story_by_conversation_id_and_order(self,conversation_id: int,itcode: str)->List[BizUserStory]:
        """根据conversation_id查询最新版本的用户故事列表并且按照order降序返回"""
        with Session(self.db_engine) as session:
            sub_stmt = (
                select(BizUserStory.uuid)
                .where(
                    BizUserStory.conversation_id == conversation_id,
                    BizUserStory.is_deleted == False,
                    BizUserStory.create_by == current_itcode.get()
                )
            )
            uuid_list = [row for row in session.exec(sub_stmt).all()]
            if not uuid_list:
                return []
            # 再查出这些uuid且version=-1的用户故事1
            stmt = (
                select(BizUserStory)
                .where(
                    BizUserStory.uuid.in_(uuid_list),
                    BizUserStory.version == -1
                )
            )\
            .order_by(desc(BizUserStory.order))
            return list(session.exec(stmt).all())

    def query_user_story_by_uuid(self,uuid: str)->List[BizUserStory]:
        """根据uuid查询用户故事,按照version降序返回"""
        with Session(self.db_engine) as session:
            statement = select(BizUserStory).where(
                BizUserStory.uuid == uuid,
                BizUserStory.is_deleted == False
            )\
            .order_by(desc(BizUserStory.version))  # 添加降序排序
            return list(session.exec(statement).all())

    def get_story_ids_by_uuids(self, uuids: List[str]) -> List[int]:
        """通过uuid列表获取对应的所有的id列表"""
        with Session(self.db_engine) as session:
            stmt = (
                select(BizUserStory.id)
                .where(
                    BizUserStory.uuid.in_(uuids),
                    BizUserStory.create_by == current_itcode.get(),
                    BizUserStory.is_deleted == False
                )
            )
            return session.exec(stmt).all()

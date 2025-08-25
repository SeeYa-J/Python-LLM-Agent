# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
# dao/biz_jira_upload_record_dao.py
from typing import List, Optional
from sqlmodel import Session, select
from dao.base_dao import BaseDAO
from models.business_entities import BizJiraUploadRecord
from utils.dependency_injection import repository
from datetime import datetime
from utils.response_utils import ApiResponse
from config.context import current_itcode


@repository
class BizJiraUploadRecordDAO(BaseDAO[BizJiraUploadRecord]):
    """JIRA上传记录 DAO"""

    def __init__(self, db_engine):
        super().__init__(db_engine, BizJiraUploadRecord)

    def batch_insert_upload_records2(self, upload_results: List[BizJiraUploadRecord]) -> List[BizJiraUploadRecord]:
        """
        批量插入上传记录
        """
        with Session(self.db_engine) as session:
            session.add_all(upload_results)
            session.commit()
            for record in upload_results:
                session.refresh(record)
            return upload_results

    def batch_insert_upload_records(self, upload_results: List[dict]) -> List[BizJiraUploadRecord]:
        """
        批量插入上传记录
        """
        with Session(self.db_engine) as session:
            records = []
            current_time = datetime.now()

            for result in upload_results:
                record = BizJiraUploadRecord(
                    story_id=result.get('story_id'),
                    jira_project_id=result.get('jira_project_id'),
                    jira_issue_key=result.get('jira_key'),  # 可以为None
                    jira_summary=result.get('summary'),  # 可以为None
                    status=result.get('status') or 'unknown',  # 必填，给默认值
                    error_msg=result.get('error_msg'),  # 可以为None
                    create_time=result.get('create_time') or current_time,
                    modify_time=result.get('modify_time') or current_time,
                    create_by=current_itcode.get(),  # 必填，给默认值
                    modify_by=current_itcode.get(),  # 必填，给默认值
                    is_deleted=False,
                    url = result.get('url')
                )
                records.append(record)
                session.add(record)

            session.commit()

            for record in records:
                session.refresh(record)

            return records
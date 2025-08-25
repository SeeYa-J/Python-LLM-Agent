# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
from typing import Optional
from datetime import datetime
from sqlmodel import Field
from models.base_entity import BaseEntity


class BizUser(BaseEntity, table=True):
    """
    用户表
    """
    __tablename__ = "biz_user"

    id: Optional[int] = Field(default=None, primary_key=True, description="主键，自增，唯一标识用户")
    itcode: str = Field(max_length=50, unique=True, description="企业内部AD系统用户标识（唯一）")
    last_login_time: Optional[datetime] = Field(default=None, description="记录用户最近登录时间")
    jira_token: str = Field(max_length=50, unique=True,description="jira用来认证的token")

class AiChatSession(BaseEntity, table=True):
    """
    AI聊天会话表
    """
    __tablename__ = "ai_chat_session"

    id: Optional[int] = Field(default=None, primary_key=True, description="主键，自增")
    project_id: Optional[int] = Field(default=None, description="外键，对应biz_jira_project的id")
    session_id: str = Field(max_length=100, description="aiforce会话id")
    summary: Optional[str] = Field(max_length=100, description="存储第一轮对话的总结内容")
    addition_info: Optional[str] = Field(max_length=100, description="储存用户附加文件的（ai_upload_document）id，逗号分隔")
    user_story_uuid: Optional[str] = Field(default=None, max_length=100, description="标记是否是user_story小卡片上的对话")
    status: str = Field(max_length=20, default="进行中", description="枚举值（\"进行中\"、\"已结束\"），记录对话状态")
    project_key: Optional[str] = Field(default=None, max_length=20, description="project维度，和CMDB ID和知识库唯一绑定")


class AiChatSessionDetail(BaseEntity, table=True):
    """
    AI聊天会话详情表
    """
    __tablename__ = "ai_chat_session_detail"

    id: Optional[int] = Field(default=None, primary_key=True, description="主键，自增")
    conversation_id: int = Field(description="外键，关联历史对话表")
    session_id: int = Field(description="关联历史对话表中的session_id")
    user_flag: str = Field(max_length=10, description="0-系统消息，1-用户消息")
    message_content: str = Field(description="消息具体内容")
    prompt_id: Optional[int] = Field(default=None, description="外键，关联系统提示词表，可为null")
    ref_document_id: Optional[str] = Field(max_length=100,default=None, description="外键，关联上传文档表，可为null")
    reg_document_id: Optional[str] = Field(max_length=20, description="AIforce返回rag出来的文档，关联ai_aiforce_rag_doc的id，多个用逗号分隔")
    round_number: int = Field(description="对话轮次编号，从1开始递增")


class AiSystemPrompt(BaseEntity, table=True):
    """
    AI系统提示词表
    """
    __tablename__ = "ai_system_prompt"

    id: Optional[int] = Field(default=None, primary_key=True, description="主键，自增")
    jira_project_id: int = Field(description="关联biz_jira_project.id")
    domain_id: int = Field(description="关联biz_domain.id")
    title: str = Field(max_length=100, description="提示词标题")
    content: str = Field(max_length=1000, description="提示词具体内容")
    is_predefined: bool = Field(default=False, description="0-非预制，1-预制")
    description: Optional[str] = Field(max_length=200, description="提示词用途场景说明")
    project_key: Optional[str] = Field(default=None, max_length=20, description="project维度，和CMDB ID和知识库唯一绑定")


class AiUploadDocument(BaseEntity, table=True):
    """
    AI上传文档表
    """
    __tablename__ = "ai_upload_document"

    id: Optional[int] = Field(default=None, primary_key=True, description="主键，自增")
    conversation_id: int = Field(default=None, description="外键，关联历史对话表")
    document_name: str = Field(max_length=255, description="文档名称")
    file_path: str = Field(max_length=500, description="文档存储路径")
    file_size: int = Field(description="文档大小（字节）")
    file_type: str = Field(max_length=50, description="文档类型（如pdf、docx）")
    file_context: Optional[str] = Field(default=None, description="文档内容")


class BizJiraProject(BaseEntity, table=True):
    """
    业务JIRA项目表（示例表）
    """
    __tablename__ = "biz_jira_project"

    id: Optional[int] = Field(default=None, primary_key=True, description="主键，自增")
    project_url: str = Field(max_length=100, description="项目名称")
    project_key: str = Field(max_length=20, description="项目标识")
    description: Optional[str] = Field(max_length=500, description="项目描述")
    service_id: str = Field(default=None, description="AI FORCE的智能体id")


class BizDomain(BaseEntity, table=True):
    """
    业务域表（示例表）
    """
    __tablename__ = "biz_domain"

    id: Optional[int] = Field(default=None, primary_key=True, description="主键，自增")
    domain_name: str = Field(max_length=100, description="域名称")
    domain_code: str = Field(max_length=50, description="域编码")
    description: Optional[str] = Field(max_length=500, description="域描述")


class BizUserStory(BaseEntity, table=True):
    """
    User Story表
    """
    __tablename__ = "biz_user_story"

    id: Optional[int] = Field(default=None, primary_key=True, description="主键，自增")
    conversation_id: int = Field(description="外键，关联历史对话表")
    jira_id: Optional[int] = Field(default=None, description="外键，关联jira上传记录表，如果没关联代表没上传")
    jira_summary: str = Field(max_length=255, description="卡片标题")
    jira_description: Optional[str] = Field(max_length=500, description="卡片描述")
    jira_background: Optional[str] = Field(default=None, max_length=500, description="背景说明")
    jira_acceptance_criteria: Optional[str] = Field(max_length=500, description="验收标准")
    jira_story_points: Optional[int] = Field(default=None, description="Story Points（整数）")
    jira_priority: Optional[str] = Field(default=None, max_length=20, description="优先级 High/Medium/Low")
    jira_dependency: Optional[str] = Field(default=None, max_length=500, description="依赖项")
    jira_performance: Optional[str] = Field(default=None, max_length=500, description="性能要求")
    jira_solution: Optional[str] = Field(default=None, max_length=1000, description="技术方案/解决思路")
    jira_ui_ux_design: Optional[str] = Field(default=None, max_length=500, description="UI/UX 设计说明或链接")
    jira_assignee: Optional[str] = Field(default=None, max_length=50, description="被指派人 itcode")
    jira_planned_start: Optional[datetime] = Field(default=None, max_length=20, description="计划开始时间 dd/MMM/yy h:mm a")
    jira_planned_end: Optional[datetime] = Field(default=None, max_length=20, description="计划结束时间 dd/MMM/yy h:mm a")
    generate_time: datetime = Field(default=datetime.now(),description="卡片生成时间（保留，与记录创建时间区分）")
    is_selected: bool = Field(default=False, description="0-未选中，1-已选中，默认0")
    version: int = Field(default=-1, description="卡片版本，-1为最新，正整数为历史版本")
    uuid: str = Field(max_length=100, description="标识单个卡片的id，可以有不同的version")
    order: int = Field(description="创建时的先后顺序")



class BizJiraUploadRecord(BaseEntity, table=True):
    """
    Jira上传记录表
    """
    __tablename__ = "biz_jira_upload_record"

    id: Optional[int] = Field(default=None, primary_key=True, description="主键，自增")
    story_id: int = Field(description="关联user story的id")
    jira_project_id: int = Field(description="关联biz_jira_project的id")
    jira_issue_key: Optional[str] = Field(max_length=500, description="比如LGVMDS-246")
    jira_summary: Optional[str] = Field(max_length=100, description="jira单据的标题")
    status: str = Field(max_length=20, description="枚举值（\"成功\"、\"失败\"）")
    error_msg: Optional[str] = Field(max_length=500, description="上传失败时记录错误原因")
    url: Optional[str] = Field(max_length=500, description="上传链接")
    project_key: Optional[str] = Field(default=None, max_length=20, description="project维度，和CMDB ID和知识库唯一绑定")


class AiAiforceRagDoc(BaseEntity, table=True):
    """
    AIforce RAG文档表
    """
    __tablename__ = "ai_aiforce_rag_doc"

    id: Optional[int] = Field(default=None, primary_key=True, description="主键，自增")
    file_name: str = Field(max_length=100, description="文件名称")
    file_path: str = Field(max_length=200, description="文件路径")

# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0
# See LICENSE.md file for permissions.
import json
from typing import List, Optional
from config_service import ConfigService
from dao.ai_prompt_dao import AiSystemPromptDAO
from dao.chat_session_dao import AiChatSessionDAO
from models.business_entities import BizUserStory
from dao.user_story_dao import BizUserStoryDAO
from utils.dependency_injection import service
from utils.response_utils import ApiResponse
import csv
import uuid
from datetime import datetime
import os
import pandas as pd
@service
class UserStoryService:
    """用户故事业务层服务"""
    user_story_dao: BizUserStoryDAO
    chat_session_dao: AiChatSessionDAO
    ai_prompt_dao: AiSystemPromptDAO
    config_service: ConfigService

    def __init__(self):
        pass

    def update_user_story(self,itcode:str, uuid: str, story_data: dict, operator: str) -> Optional[BizUserStory]:
        """更新用户故事 - 通过新建副本并更新的方式"""
        current_story = self.user_story_dao.find_user_story_by_uuid(uuid)
        if not current_story:
            return None

        max_version = self.user_story_dao.get_max_version_by_uuid(uuid)

        current_story.version = max_version + 1
        self.user_story_dao.update(current_story, operator)

        new_story = self._create_story_copy(current_story)

        for key, value in story_data.items():
            if hasattr(new_story, key):
                setattr(new_story, key, value)

        new_story.version = -1

        return self.user_story_dao.create(new_story, operator)

    def _create_story_copy(self, original_story: BizUserStory) -> BizUserStory:
        """创建用户故事的深拷贝"""
        # 获取原对象的所有属性，排除自动管理的字段
        story_dict = {}
        exclude_fields = {'id', 'create_time','create_by', 'modify_time','modify_by'}  # 这些字段将由BaseDAO.create()自动设置

        for column in BizUserStory.__table__.columns:
            if column.name not in exclude_fields:
                story_dict[column.name] = getattr(original_story, column.name)

        new_story = BizUserStory(**story_dict)
        return new_story

    def exhibit_user_story(self,itcode: str,conversation_id:int,operator) -> List[BizUserStory]:
        return self.user_story_dao.find_user_story_by_conversation_id(itcode,conversation_id)

    def batch_delete_selected_stories(self,itcode:str,uuids:List[str],operator:str) -> int:
        """批量软删除uuids对应的用户故事"""
        story_ids = self.user_story_dao.get_story_ids_by_uuids(uuids)
        deleted_count = 0
        for story_id in story_ids:
            if self.user_story_dao.soft_delete(story_id, operator):
                deleted_count += 1

        return deleted_count

    def export_to_excel(self, itcode: str, uuids: List[str]) -> tuple[str, str]:
        """导出用户故事到Excel"""
        stories = self.user_story_dao.find_user_story_by_uuids(itcode, uuids)
        # 生成文件
        file_name = f"user_stories_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        os.makedirs("temp", exist_ok=True)
        file_path = os.path.join("temp", file_name)

        if stories:
            data = []
            for story in stories:
                data.append({
                    'ID': story.id,
                    'Conversation_ID': story.conversation_id,
                    'JIRA_ID': story.jira_id,
                    'JIRA_Summary': story.jira_summary,
                    'JIRA_Description': story.jira_description,
                    'JIRA_Acceptance_Criteria': story.jira_acceptance_criteria,
                    'Generate_Time': story.generate_time,
                    'Is_Selected': story.is_selected,
                    'Version': story.version,
                    'UUID': story.uuid,
                    'Create_Time': story.create_time,
                    'Modify_Time': story.modify_time,
                    'Create_By': story.create_by,
                    'Modify_By': story.modify_by,
                    'Is_Deleted': story.is_deleted,
                    'JIRA_Background': story.jira_background,
                    'JIRA_Story_Points': story.jira_story_points,
                    'JIRA_Priority': story.jira_priority,
                    'JIRA_Dependency': story.jira_dependency,
                    'JIRA_Performance': story.jira_performance,
                    'JIRA_Solution': story.jira_solution,
                    'JIRA_UI_UX_Design': story.jira_ui_ux_design,
                    'JIRA_Assignee': story.jira_assignee,
                    'JIRA_Planned_Start': story.jira_planned_start,
                    'JIRA_Planned_End': story.jira_planned_end
                })
        else:
            data = [{"Message": "未找到匹配的用户故事"}]
        df = pd.DataFrame(data)
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='User_Stories', index=False)
            # 调整列宽
            for col in writer.sheets['User_Stories'].columns:
                writer.sheets['User_Stories'].column_dimensions[col[0].column_letter].width = 20

        return file_path, file_name

    def get_divide_user_story_prompt(self,round_number: int,user_input: str,original_scheme: str) -> str:
        """获取生成用户故事提示词，round_number为1则获取创建用户故事提示词，大于1则获取新增用户故事提示词"""
        # 根据对话轮次选择提示词
        if round_number==1:
            divide_user_story_prompt_id = self.config_service.data["prompt_id"]["divide_user_story_prompt_id"]
        elif round_number==-1:
            divide_user_story_prompt_id = self.config_service.data["prompt_id"]["update_user_story_prompt_id"]
        else:
            # 默认提示词
            divide_user_story_prompt_id = self.config_service.data["prompt_id"]["again_divide_user_story_prompt_id"]
        divide_user_story_prompt_info = self.ai_prompt_dao.get_by_id(divide_user_story_prompt_id)
        divide_user_story_prompt = divide_user_story_prompt_info.content
        if round_number==1:
            divide_user_story_prompt = divide_user_story_prompt.format(user_input=user_input)
        else:
            divide_user_story_prompt = divide_user_story_prompt.format(user_input=user_input,original_scheme=original_scheme)
        return divide_user_story_prompt

    def get_update_user_story_prompt(self,user_input: str,original_scheme: str)-> str:
        """获取修改用户故事提示词"""
        update_user_story_prompt_id = self.config_service.data["prompt_id"]["update_user_story_prompt_id"]
        update_user_story_prompt_info = self.ai_prompt_dao.get_by_id(update_user_story_prompt_id)
        update_user_story_prompt = update_user_story_prompt_info.content
        return update_user_story_prompt.format(user_input=user_input,original_scheme=original_scheme)

    def get_latest_user_story_by_conversation_id(self,conversation_id: int,itcode: str)-> List[BizUserStory]:
        """根据conversation_id获取最新的user stories"""
        return self.user_story_dao.query_user_story_by_conversation_id_and_order(conversation_id,itcode)

    def get_user_story_by_story_id(self,story_id: int=None)->BizUserStory:
        """根据story_id查询user story"""
        return self.user_story_dao.get_by_id(story_id)

    def get_json_user_story(self,user_stories:List[BizUserStory]) -> str:
        """根据conversation_id或者story_id获取最新的user story scheme(mode=0代表一般对话,mode=1代表卡片对话)"""
        # user_story = []
        # if mode==0:
        #     user_story = self.user_story_dao.query_latest_user_story_by_conversation_id(conversation_id)
        # elif mode==1:
        #     story = self.user_story_dao.get_by_id(story_id)
        #     user_story.append(story)
        result = []
        for story in user_stories:
            story_data = {}
            story_data["Summary"] = story.jira_summary
            story_data["Background"] = story.jira_background
            story_data["Description"] = story.jira_description
            story_data["Acceptance Criteria"] = story.jira_acceptance_criteria
            story_points = story.jira_story_points
            if not story_points:
                story_points = ""
            story_data["Story Points"] = story_points
            story_data["Priority"] = story.jira_priority
            dependency = story.jira_dependency
            if not dependency:
                dependency = ""
            story_data["Dependency"] = dependency
            performance = story.jira_performance
            if not performance:
                performance = ""
            story_data["Performance"] = performance
            solution = story.jira_solution
            if not solution:
                solution = ""
            story_data["Solution"] = solution
            ui_ux_design = story.jira_ui_ux_design
            if not ui_ux_design:
                ui_ux_design = ""
            story_data["UI UX Design"] = ui_ux_design
            uuid = story.uuid
            if not uuid:
                uuid = ""
            story_data["UUID"] = uuid
            result.append(story_data)
        return json.dumps(result,ensure_ascii=False)

    def get_user_story_by_json(self,user_story_str: str,operator: str,user_story_summary: str=None) -> list[dict]:
        """解析json格式的字符串user_story,返回列表数据"""
        result = []
        if user_story_str=="":
            return result
        user_stories = json.loads(user_story_str)
        # 处理表头和值
        for user_story in user_stories:
            data = {}
            for key,value in user_story.items():
                # 新增新键，值为旧键的值
                if key!="UUID":
                    new_key = "jira_"+key.strip().lower().replace(" ", "_")
                else:
                    new_key = "uuid"
                # 对新键特殊数据进行一些处理
                if new_key=="jira_story_points" and not isinstance(value, int):
                    value = int(value[0])
                elif new_key=="jira_priority" and len(value)>20:
                    value = value[:20]
                elif new_key=="jira_background" and user_story_summary is not None:
                    value = "background\n"+value+"\n\n"+"user_story整体概述\n"+user_story_summary
                data[new_key] = value
            # TBD数据
            data["jira_assignee"] = operator
            data["jira_planned_start"] = datetime.now()
            data["jira_planned_end"] = datetime.now()
            result.append(data)
        # jira_background添加所有user_story的jira_summary
        if user_story_summary is not None:
            jira_summaries = [item["jira_summary"] for item in result]
            for data in result:
                # 检查键是否存在，避免 KeyError
                if "jira_background" in data:
                    data["jira_background"] += "\n\nuser_story列表:"
                    for i in range(len(jira_summaries)):
                        data["jira_background"] += jira_summaries[i]
                        # 添加分隔符
                        if i < len(jira_summaries)-1:
                            data["jira_background"] +=","
        return result

    def save_user_story(self,conversation_id: int,round_number: int,user_story_list: List[dict],operator: str)->List[BizUserStory]:
        """保存对话过程中的user_story"""
        result = []
        if round_number==1:
            # 第一轮对话批量插入user_story
            i = 1
            for story_data in user_story_list:
                story_data["conversation_id"] = conversation_id
                story_data["version"] = -1
                story_data["uuid"] = str(uuid.uuid1())
                story_data["order"] = i
                i += 1
                user_story = BizUserStory(**story_data)
                biz_user_story = self.user_story_dao.create(user_story, operator)
                result.append(biz_user_story)
        else:
            # 多轮对话应该修改（多个）
            for story_data in user_story_list:
                # 按照是否新增分类处理
                if story_data["jira_is_new"]=="false":
                    story_uuid = story_data["uuid"]
                    # 查询version最大版本号
                    user_story = self.user_story_dao.query_user_story_by_uuid(story_uuid)
                    max_version = user_story[0].version
                    last_user_story_id = user_story[-1].id
                    order = user_story[-1].order
                    # 修改最新的user_story的版本号
                    last_user_story = self.user_story_dao.get_by_id(last_user_story_id)
                    last_user_story.version = max_version+1
                    new_user_story = self.user_story_dao.update(last_user_story,operator)
                    if not new_user_story:
                        raise ValueError("更新版本号失败")
                    # 插入最新数据
                    del story_data["jira_is_new"]
                    story_data["conversation_id"] = conversation_id
                    story_data["version"] = -1
                    story_data["order"] = order
                    story_data = BizUserStory(**story_data)
                    biz_user_story = self.user_story_dao.create(story_data,operator)
                    result.append(biz_user_story)
                else:
                    del story_data["jira_is_new"]
                    story_data["conversation_id"] = conversation_id
                    story_data["version"] = -1
                    story_data["uuid"] = str(uuid.uuid1())
                    user_stories = self.user_story_dao.query_user_story_by_conversation_id_and_order(conversation_id,operator)
                    max_order = user_stories[0].order
                    order = max_order+1
                    story_data["order"] =order
                    user_story = BizUserStory(**story_data)
                    biz_user_story = self.user_story_dao.create(user_story, operator)
                    result.append(biz_user_story)
        return result
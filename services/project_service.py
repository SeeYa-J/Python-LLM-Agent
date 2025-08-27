from typing import List, Optional
from dao.project_dao import BizJiraProjectDAO
from models.business_entities import BizJiraProject
from utils.dependency_injection import service
import json

@service
class ProjectService:
    """处理project的服务层"""
    project_dao: BizJiraProjectDAO

    def __init__(self):
        pass

    def query_project_by_creator(self)->List[BizJiraProject]:
        """根据创始人查询project"""
        return self.project_dao.find_by_creator()

    def get_project_id_return_data(self,projects: List[BizJiraProject])->dict:
        """返回根据itcode查询project的前端数据"""
        result = {}
        result["projects"] = []
        for project in projects:
            data = {}
            data["id"] = project.id
            data["project_key"] = project.project_key
            data["project_description"] = project.description
            result["projects"].append(data)
        return result

    def query_project_by_project_key(self,project_key:str)->BizJiraProject:
        """根据project_id以及创建人查询project"""
        return self.project_dao.find_by_project_key(project_key)

    def get_project_return_data(self,project:BizJiraProject)->dict:
        """返回查询project详情的前端数据"""
        result = {}
        result["id"] = project.id
        result["project_key"] = project.project_key
        result["project_description"] = project.description
        result["service_id"] = project.service_id
        return result
# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
from typing import Any, Optional, Dict, List
from datetime import datetime


class ApiResponse:
    """API响应封装工具类"""

    @staticmethod
    def success(data: Any = None, message: str = "操作成功",conversation_id: int = None,session_id: str=None) -> Dict[str, Any]:
        """成功响应"""
        response = {
            "success": True,
            "message": message
        }
        if conversation_id is not None:
            response["conversation_id"] = conversation_id
        if session_id is not None:
            response["session_id"] = session_id
        if data is not None:
            response["data"] = ApiResponse._serialize_data(data)
        return response

    @staticmethod
    def error(message: str = "操作失败") -> Dict[str, Any]:
        """错误响应"""
        return {
            "success": False,
            "message": message
        }

    @staticmethod
    def list_success(data: List[Any], total: int = None, message: str = "查询成功") -> Dict[str, Any]:
        """列表查询成功响应"""
        serialized_data = [ApiResponse._serialize_data(item) for item in data]
        response = {
            "success": True,
            "data": serialized_data,
            "message": message
        }
        if total is not None:
            response["total"] = total
        else:
            response["total"] = len(data)
        return response


    @staticmethod
    def _serialize_data(obj: Any) -> Any:
        """通用数据序列化方法"""
        if obj is None:
            return None

        # 如果是基本类型，直接返回
        if isinstance(obj, (str, int, float, bool)):
            return obj

        # 如果是datetime对象，转换为ISO格式字符串
        if isinstance(obj, datetime):
            return obj.isoformat()

        # 如果是列表，递归序列化每个元素
        if isinstance(obj, list):
            return [ApiResponse._serialize_data(item) for item in obj]

        # 如果是字典，递归序列化每个值
        if isinstance(obj, dict):
            return {key: ApiResponse._serialize_data(value) for key, value in obj.items()}

        # 如果是SQLModel对象或其他有属性的对象，转换为字典
        if hasattr(obj, '__dict__'):
            result = {}
            for key, value in obj.__dict__.items():
                # 跳过私有属性和SQLAlchemy内部属性
                if not key.startswith('_'):
                    result[key] = ApiResponse._serialize_data(value)
            return result

        # 如果对象有model_dump方法（Pydantic模型），使用它
        if hasattr(obj, 'model_dump'):
            return obj.model_dump()

        # 如果对象有dict方法（SQLModel），使用它
        if hasattr(obj, 'dict'):
            return obj.dict()

        # 最后尝试转换为字符串
        return str(obj)

from fastapi.responses import JSONResponse

from api.api_conversation import ApiConversation
from api.api_fastapi import ApiFastAPI
from api.api_project import ApiProject
from api.api_userstory import ApiUserStory
from utils.dependency_injection import setup_dependency_injection
from utils.re_util import match_any_pattern
from config.context import current_itcode
from config_service import ConfigService
from logger import HaivenLogger
from fastapi import FastAPI
from starlette.requests import Request


class RqServer:
    exclude_paths = [
        "/health",
        "/docs",
        "/redoc",
        "/swagger-resource/*",
        "/openapi.json",
    ]

    def __init__(self, config_service: ConfigService):
        self.config_service = config_service
        setup_dependency_injection(config_service.db_engine) #初始化容器，完成 service、repository、controller注入


    def _log_request_info(self, request: Request, body: bytes):
        """记录请求信息为单行日志"""
        try:
            import json
            from urllib.parse import parse_qs

            # 基本信息
            method = request.method #获取请求方法
            url = str(request.url) #请求url
            # 根据 request.headers #表头信息 获取内容
            content_type = request.headers.get("content-type", "").lower()

            # 处理请求体
            payload_info = "no-body"
            if body:
                if "application/json" in content_type:
                    try:
                        payload = json.loads(body.decode('utf-8'))
                        payload_info = f"json:{json.dumps(payload, ensure_ascii=False)}"
                    except json.JSONDecodeError:
                        payload_info = f"invalid-json:{body.decode('utf-8', errors='ignore')[:100]}"

                elif "application/x-www-form-urlencoded" in content_type:
                    form_data = parse_qs(body.decode('utf-8'))
                    payload_info = f"form:{dict(form_data)}"

                elif "multipart/form-data" in content_type:
                    payload_info = f"multipart:{len(body)}bytes"

                else:
                    payload_info = f"raw({content_type}):{body.decode('utf-8', errors='ignore')[:100]}"

            # 单行日志输出
            HaivenLogger.get().logger.info(f"Request: {method} {url} | Payload: {payload_info}")

        except Exception as e:
            HaivenLogger.get().logger.error(f"Error logging request: {e}")

    def add_logging_middleware(self, app):
        """添加请求日志中间件"""
        @app.middleware("http")
        async def logging_middleware(request: Request, call_next):
            try:
                # 获取请求体
                body = await request.body()

                # 记录请求信息
                self._log_request_info(request, body)

            except Exception as e:
                HaivenLogger.get().logger.error(f"Error reading request payload: {e}")

            response = await call_next(request)
            return response

    def add_auth_middleware(self, app):
        """添加认证中间件"""
        @app.middleware("http")
        async def auth_middleware(request: Request, call_next):
            # 从 header 获取 itcode
            itcode = request.headers.get("x-user-id")
            if not itcode and not match_any_pattern(request.url.path, RqServer.exclude_paths):
                return JSONResponse(status_code=401,
                                    content={"path": request.url.path, "message": "Missing x-user-id header"})
            HaivenLogger.get().logger.info(f"itcode from header: {itcode}")

            # 设置上下文变量
            token = current_itcode.set(itcode)

            try:
                response = await call_next(request)
            finally:
                # 请求处理完成后清理上下文
                current_itcode.reset(token)

            return response


    def add_middleware(self, app):
        # 按顺序添加中间件
        # self.add_logging_middleware(app)
        self.add_auth_middleware(app)

    def add_endpoints(self, app):
        ApiFastAPI(app)
        ApiUserStory(app)
        ApiConversation(app)
        ApiProject(app)


    def create(self):
        app = FastAPI(docs_url=None, redoc_url=None)# 禁用默认文档

        self.add_middleware(app)
        self.add_endpoints(app)

        return app

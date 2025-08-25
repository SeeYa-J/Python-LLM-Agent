from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse


class ApiFastAPI:
    def __init__(self, app):
        self._register_routes(app)
        app.mount("/swagger-resource", StaticFiles(directory="resources/static/swagger"), name="swagger-resource")

    def _register_routes(self, app):

        @app.get("/health")
        async def health_check():
            """
            心跳检测API - 根路径健康检查
            """
            return JSONResponse(
                {
                    "status": "ok",
                    "message": "Haiven API is running",
                },
                status_code=200
            )

        @app.get("/docs", include_in_schema=False)
        async def custom_swagger_ui_html():
            return get_swagger_ui_html(
                openapi_url=app.openapi_url,
                title=app.title + " - Swagger UI",
                oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
                swagger_js_url="/swagger-resource/swagger-ui-bundle.js",
                swagger_css_url="/swagger-resource/swagger-ui.css",
            )

        @app.get("/redoc", include_in_schema=False)
        async def redoc_html():
            return get_redoc_html(
                openapi_url=app.openapi_url,
                title=app.title + " - ReDoc",
                redoc_js_url="/swagger-resource/redoc.standalone.js",
            )
# # © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
# import io
# import os.path
# import re
# import uuid
# from typing import List
# from fastapi import FastAPI, HTTPException, Request
# from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
# from fastapi import File, Form, UploadFile
# from PIL import Image
#
# from pydantic import BaseModel
# from config.constants import CSV_GENERATION_INFO, FILE_NOTE1, FILE_NOTE2
# from embeddings.documents import KnowledgeDocument
# from knowledge_manager import KnowledgeManager
# from llms.chats import ChatManager, ChatOptions, StreamingChat
# from llms.model_config import ModelConfig
# from llms.image_description_service import ImageDescriptionService
# from prompts.prompts import PromptList
# from prompts.inspirations import InspirationsManager
# from llms.aiforce_util import AiforceUtil
#
# from config_service import ConfigService
# from disclaimer_and_guidelines import DisclaimerAndGuidelinesService
# from logger import HaivenLogger
# from loguru import logger
# import hashlib
# import json
# from utils.PDFUtils import PPTUtil
# from utils.stream_util import StreamUtil
#
#
# class PromptRequestBody(BaseModel):
#     userinput: str = None
#     promptid: str = None
#     chatSessionId: str = None
#     contexts: List[str] = None
#     document: List[str] = None
#     json: bool = False
#     userContext: str = None
#
# class MermaidRequestBody(BaseModel):
#     userinput: str = None
#     userContext:str = None
#     imagePath:str = None
#     imageId: str = None
#     chatSessionId: str = None
#     json: bool = False
#
# class ImageInfoRequestBody(BaseModel):
#     imageId: str = None
#     sessionId: str = None
#
#
#
# class IterateRequest(PromptRequestBody):
#     scenarios: str
#
#
# def streaming_media_type() -> str:
#     return "text/event-stream"
#
#
# def streaming_headers(chat_session_key_value=None):
#     headers = {
#         "Connection": "keep-alive",
#         "Content-Encoding": "none",
#         "Access-Control-Expose-Headers": "X-Chat-ID",
#     }
#     if chat_session_key_value:
#         headers["X-Chat-ID"] = chat_session_key_value
#
#     return headers
#
#
# class HaivenBaseApi:
#     def __init__(
#         self,
#         app,
#         chat_manager: ChatManager,
#         model_config: ModelConfig,
#         prompt_list: PromptList,
#     ):
#         self.chat_manager = chat_manager
#         self.model_config = model_config
#         self.prompt_list = prompt_list
#
#     def get_hashed_user_id(self, request):
#         if request.session and request.session.get("user"):
#             user_id = request.session.get("user").get("email")
#             hashed_user_id = hashlib.sha256(user_id.encode("utf-8")).hexdigest()
#             return hashed_user_id
#         else:
#             return None
#
#     def stream_json_chat(
#         self,
#         prompt,
#         chat_category,
#         chat_session_key_value=None,
#         document_keys=None,
#         prompt_id=None,
#         user_identifier=None,
#         contexts=None,
#         origin_url=None,
#         model_config=None,
#         userContext=None,
#     ):
#         try:
#             def stream(chat_session_key_value, prompt):
#                 try:
#                     for chunk in AiforceUtil.send_request(prompt, "1849753300972187648", chat_session_key_value):
#                         yield json.dumps({"data": chunk}) + "\n\n"
#                 except Exception as error:
#                     if not str(error).strip():
#                         error = "Error while the model was processing the input"
#                     print(f"[ERROR]: {str(error)}")
#                     yield f"[ERROR]: {str(error)}"
#
#             chat_session_key_value, chat_session = self.chat_manager.json_chat(
#                 model_config=model_config or self.model_config,
#                 session_id=chat_session_key_value,
#                 options=ChatOptions(category=chat_category),
#             )
#
#             self.log_run(
#                 chat_session,
#                 origin_url,
#                 user_identifier,
#                 chat_session_key_value,
#                 prompt_id,
#                 contexts,
#                 userContext,
#             )
#
#             return StreamingResponse(
#                 # chat_session.run(prompt),
#                 # AiforceUtil.send_request(prompt, "baosongtest", chat_session_key_value),
#                 stream(chat_session_key_value, prompt),
#                 media_type=streaming_media_type(),
#                 headers=streaming_headers(chat_session_key_value),
#             )
#
#         except Exception as error:
#             raise Exception(error)
#
#     def log_run(
#         self,
#         chat_session,
#         origin_url,
#         user_identifier,
#         chat_session_key_value,
#         prompt_id,
#         context,
#         userContext,
#     ):
#         return chat_session.log_run(
#             {
#                 "url": origin_url,
#                 "user_id": user_identifier,
#                 "session": chat_session_key_value,
#                 "prompt_id": prompt_id,
#                 "context": ",".join(context or []),
#                 "is_user_context_included": True if userContext else False,
#             }
#         )
#
#     def stream_text_chat(
#         self,
#         prompt,
#         chat_category,
#         chat_session_key_value=None,
#         document_keys=[],
#         prompt_id=None,
#         user_identifier=None,
#         contexts=None,
#         origin_url=None,
#         userContext=None,
#     ):
#         try:
#             chat_session_key_value, chat_session = self.chat_manager.streaming_chat(
#                 model_config=self.model_config,
#                 session_id=chat_session_key_value,
#                 options=ChatOptions(in_chunks=True, category=chat_category),
#             )
#
#             self.log_run(
#                 chat_session,
#                 origin_url,
#                 user_identifier,
#                 chat_session_key_value,
#                 prompt_id,
#                 contexts,
#                 userContext,
#             )
#             if chat_category=="boba-mermaid":
#                 stream_fn = StreamUtil.stream_mermaid
#             else:
#                 stream_fn = StreamUtil.stream_text
#             return StreamingResponse(
#                 # stream(chat_session, prompt),
#                 # AiforceUtil.send_request(prompt, "baosongtest", chat_session_key_value),
#                 stream_fn(self.model_config.config["agent"],chat_session_key_value, prompt),
#                 media_type=streaming_media_type(),
#                 headers=streaming_headers(chat_session_key_value),
#             )
#
#         except Exception as error:
#             raise Exception(error)
#     # VLM解析图片
#     def stream_image_chat(
#             self,
#             prompt,
#             image_service
#     ):
#         try:
#             # 解析传入文字获取用户输入以及图片保存地址
#             real_prompt = prompt.split("图片描述：")[0]
#             file_name = prompt.split("下载地址：temp")[1]
#             image_path = './temp' + file_name
#             with open(image_path, 'rb') as f:
#                 contents = f.read()
#             image = Image.open(io.BytesIO(contents))
#             # 传入用户输入以及图片询问VLM
#             return StreamingResponse(
#                 StreamUtil.stream_image(image,real_prompt,image_service),
#                 media_type=streaming_media_type(),
#                 headers=streaming_headers(None),
#             )
#         except Exception as error:
#             raise Exception(error)
#     # 需要意图识别的流式处理
#     def stream_intention_chat(self,
#         basis_prompt,
#         judge_prompt=None,
#         examine_prompt=None,
#         again_make_prompt=None,
#         user_input=None,
#         chat_category=None,
#         chat_session_key_value=None,
#         prompt_id=None,
#         user_identifier=None,
#         contexts=None,
#         origin_url=None,
#         userContext=None,
#     ):
#         #切换agent
#         AiforceUtil.set_config(self.model_config.config["agent"]["agent-easy"])
#         # 意图识别，判断用户对PPT制作方案是否满意
#         result = AiforceUtil.get_all_result(judge_prompt, "optimus2", str(uuid.uuid4()))
#         if result=="不满意" or chat_session_key_value==None:
#             make_flag = False
#         else:
#             make_flag = True
#         chat_session_key_value, chat_session = self.chat_manager.streaming_chat(
#             model_config=self.model_config,
#             session_id=chat_session_key_value,
#             options=ChatOptions(in_chunks=True, category=chat_category),
#         )
#
#         self.log_run(
#             chat_session,
#             origin_url,
#             user_identifier,
#             chat_session_key_value,
#             prompt_id,
#             contexts,
#             userContext,
#         )
#
#         user_data = None
#         if chat_category=="boba-ppt":
#             # 根据sessionID初始化中间数据
#             user_data = self.chat_manager.chat_session_memory.USER_CHATS[chat_session_key_value]
#             if "image" not in user_data:
#                 # 保存ppt中需要插入的图片相关信息
#                 user_data["image"]={}
#             if "last_ppt_scheme" not in user_data:
#                 # 保存上次的PPT制作方案
#                 user_data["last_ppt_scheme"] =""
#             else:
#                 # 若上次PPT制作方案已存在则转换场景为修改PPT制作方案
#                 basis_prompt = again_make_prompt
#             return StreamingResponse(
#                 StreamUtil.stream_ppt(model_config=self.model_config.config["agent"],
#                                       chat_session_key_value=chat_session_key_value,
#                                       prompt=basis_prompt,
#                                       make_flag=make_flag,
#                                       user_input=user_input,
#                                       user_ppt_data=user_data,
#                                       is_examine=True,
#                                       examine_ppt_prompt=examine_prompt),
#                 media_type=streaming_media_type(),
#                 headers=streaming_headers(chat_session_key_value),
#             )
#         elif chat_category=="boba-story":
#             # 根据sessionID初始化中间数据
#             user_data = self.chat_manager.chat_session_memory.USER_CHATS[chat_session_key_value]
#             if "last_user_story_scheme" not in user_data:
#                 # 保存上次的PPT制作方案
#                 user_data["last_user_story_scheme"] = ""
#             return StreamingResponse(
#                 StreamUtil.stream_user_story(chat_session_key_value=chat_session_key_value,
#                                              prompt=basis_prompt,
#                                              query_prompt=examine_prompt,
#                                              model_config=self.model_config.config["agent"],
#                                              make_flag=make_flag,
#                                              user_story_data=user_data,
#                                              project_name="SMTGETCS"),
#                 media_type=streaming_media_type(),
#                 headers=streaming_headers(chat_session_key_value),
#             )
#
#
# class ApiBasics(HaivenBaseApi):
#     def __init__(
#         self,
#         app: FastAPI,
#         chat_manager: ChatManager,
#         model_config: ModelConfig,
#         prompts_guided: PromptList,
#         knowledge_manager: KnowledgeManager,
#         prompts_chat: PromptList,
#         prompts_diagrams: PromptList,
#         image_service: ImageDescriptionService,
#         config_service: ConfigService,
#         disclaimer_and_guidelines: DisclaimerAndGuidelinesService,
#         inspirations_manager: InspirationsManager,
#     ):
#         super().__init__(app, chat_manager, model_config, prompts_guided)
#         self.inspirations_manager = inspirations_manager
#         self.prompts_chat = prompts_chat
#         self.prompts_diagrams = prompts_diagrams
#
#         @app.get("/health")
#         @logger.catch(reraise=True)
#         def health_check(request: Request):
#             """
#             心跳检测API - 根路径健康检查
#             """
#             return JSONResponse(
#                 {
#                     "status": "ok",
#                     "message": "Haiven API is running",
#                 },
#                 status_code=200
#             )
#
#         @app.get("/api/models")
#         @logger.catch(reraise=True)
#         def get_models(request: Request):
#             try:
#                 embeddings = config_service.load_embedding_model()
#                 vision = config_service.get_image_model()
#                 chat = config_service.get_chat_model()
#                 return JSONResponse(
#                     {
#                         "chat": {
#                             "id": chat.id,
#                             "name": chat.name,
#                         },
#                         "vision": {
#                             "id": vision.id,
#                             "name": vision.name,
#                         },
#                         "embeddings": {
#                             "id": embeddings.id,
#                             "name": embeddings.name,
#                         },
#                     }
#                 )
#
#             except Exception as error:
#                 HaivenLogger.get().error(str(error))
#                 raise HTTPException(
#                     status_code=500, detail=f"Server error: {str(error)}"
#                 )
#
#         @app.get("/api/prompts")
#         @logger.catch(reraise=True)
#         def get_prompts(request: Request):
#             try:
#                 response_data = prompts_chat.get_prompts_with_follow_ups()
#                 return JSONResponse(response_data)
#
#             except Exception as error:
#                 HaivenLogger.get().error(str(error))
#                 raise HTTPException(
#                     status_code=500, detail=f"Server error: {str(error)}"
#                 )
#
#         @app.get("/api/disclaimer-guidelines")
#         @logger.catch(reraise=True)
#         def get_disclaimer_and_guidelines(request: Request):
#             try:
#                 if not disclaimer_and_guidelines.is_enabled:
#                     return JSONResponse({"enabled": False, "title": "", "content": ""})
#
#                 response_data = json.loads(
#                     disclaimer_and_guidelines.fetch_disclaimer_and_guidelines()
#                 )
#                 response_data["enabled"] = True
#                 return JSONResponse(response_data)
#
#             except Exception as error:
#                 HaivenLogger.get().error(str(error))
#                 raise HTTPException(
#                     status_code=500, detail=f"Server error: {str(error)}"
#                 )
#
#         @app.get("/api/knowledge/snippets")
#         @logger.catch(reraise=True)
#         def get_knowledge_snippets(request: Request):
#             try:
#                 all_contexts = (
#                     knowledge_manager.knowledge_base_markdown.get_all_contexts()
#                 )
#                 response_data = []
#                 for key, context_info in all_contexts.items():
#                     response_data.append(
#                         {
#                             "context": key,
#                             "title": context_info.metadata["title"],
#                             "snippets": {"context": context_info.content},
#                         }
#                     )
#
#                 response_data.sort(key=lambda x: x["context"])
#
#                 return JSONResponse(response_data)
#
#             except Exception as error:
#                 HaivenLogger.get().error(str(error))
#                 raise HTTPException(
#                     status_code=500, detail=f"Server error: {str(error)}"
#                 )
#
#         @app.get("/api/knowledge/documents")
#         @logger.catch(reraise=True)
#         def get_knowledge_documents(request: Request):
#             try:
#                 response_data = []
#                 documents: List[KnowledgeDocument] = (
#                     knowledge_manager.knowledge_base_documents.get_documents()
#                 )
#
#                 for document in documents:
#                     response_data.append(
#                         {
#                             "key": document.key,
#                             "title": document.title,
#                             "description": document.description,
#                             "source": document.get_source_title_link(),
#                         }
#                     )
#
#                 return JSONResponse(response_data)
#
#             except Exception as error:
#                 HaivenLogger.get().error(str(error))
#                 raise HTTPException(
#                     status_code=500, detail=f"Server error: {str(error)}"
#                 )
#
#         @app.post("/api/prompt")
#         @logger.catch(reraise=True)
#         def chat(request: Request, prompt_data: PromptRequestBody):
#             origin_url = request.headers.get("referer")
#             try:
#                 stream_fn = self.stream_text_chat
#                 # 获取提示词ID
#                 mermaid_prompt_id = os.environ.get("MERMAID_PROMPT_ID", "")
#                 image_prompt_id = os.environ.get("IMAGE_PROMPT_ID", "")
#                 ppt_prompt_id = os.environ.get("PPT_PROMPT_ID", "")
#                 judge_make_ppt_prompt_id = os.environ.get("JUDGE_MAKE_PPT_PROMPT_ID", "")
#                 again_make_ppt_prompt_id = os.environ.get("AGAIN_MAKE_PPT_PROMPT_ID", "")
#                 examine_ppt_prompt_id = os.environ.get("EXAMINE_PPT_PROMPT_ID", "")
#                 divide_user_story_prompt_id = os.environ.get("DIVIDE_USER_STORY_PROMPT_ID","")
#                 use_mcp_prompt_id = os.environ.get("USE_MCP_PROMPT_ID","")
#                 if prompt_data.promptid:
#                     prompts = (
#                         prompts_guided
#                         if prompt_data.promptid.startswith("guided-")
#                         else prompts_chat
#                     )
#                     rendered_prompt, _ = prompts.render_prompt(
#                         active_knowledge_contexts=prompt_data.contexts,
#                         prompt_choice=prompt_data.promptid,
#                         user_input=prompt_data.userinput,
#                         additional_vars={},
#                         warnings=[],
#                         user_context=prompt_data.userContext,
#                     )
#                     if prompts.produces_json_output(prompt_data.promptid):
#                         stream_fn = self.stream_json_chat
#                 else:
#                     rendered_prompt = prompt_data.userinput
#
#                 if prompt_data.json is True:
#                     stream_fn = self.stream_json_chat
#
#                 prompt = rendered_prompt
#                 session_id = prompt_data.chatSessionId
#                 document = prompt_data.document
#                 promptid = prompt_data.promptid
#                 user_id = self.get_hashed_user_id(request)
#                 contexts = prompt_data.contexts
#                 data = prompt_data
#                 chat_category = "boba-chat"
#                 # 根据提示词ID选择不同的处理流程
#                 if prompt_data.promptid == image_prompt_id:
#                     stream_fn = self.stream_image_chat
#                     return stream_fn(
#                         prompt=prompt,
#                         image_service=image_service
#                     )
#                 elif prompt_data.promptid == ppt_prompt_id or (session_id is not None and ('ppt' in session_id)):
#                     stream_fn = self.stream_intention_chat
#                     # 获取意图识别提示词
#                     judge_prompt, _ = self.prompts_diagrams.render_prompt(
#                         active_knowledge_contexts=None,
#                         prompt_choice=judge_make_ppt_prompt_id,
#                         user_input=prompt_data.userinput,
#                         warnings=[],
#                     )
#                     # 获取检查格式提示词
#                     examine_ppt_prompt, _ = self.prompts_diagrams.render_prompt(
#                         active_knowledge_contexts=None,
#                         prompt_choice=examine_ppt_prompt_id,
#                         user_input=" ",
#                         additional_vars={"original_scheme": "{original_scheme}"},
#                         warnings=[],
#                     )
#                     # 获取修改PPT制作方案提示词
#                     if session_id is not None:
#                         again_make_prompt,_ = self.prompts_diagrams.render_prompt(
#                             active_knowledge_contexts=None,
#                             prompt_choice=again_make_ppt_prompt_id,
#                             user_input=prompt_data.userinput,
#                             additional_vars={"original_scheme": self.chat_manager.chat_session_memory.USER_CHATS[session_id]["last_ppt_scheme"]},
#                             warnings=[],
#                         )
#                     else:
#                         again_make_prompt = None
#                     # 标记类别
#                     chat_category = "boba-ppt"
#                     return stream_fn(
#                         basis_prompt=prompt,
#                         judge_prompt=judge_prompt,
#                         again_make_prompt=again_make_prompt,
#                         examine_prompt = examine_ppt_prompt,
#                         user_input=prompt_data.userinput,
#                         chat_category=chat_category,
#                         chat_session_key_value=session_id,
#                         prompt_id=promptid,
#                         user_identifier=user_id,
#                         contexts=contexts,
#                         userContext=data.userContext,
#                         origin_url=origin_url,
#                     )
#                 elif prompt_data.promptid == divide_user_story_prompt_id or (session_id is not None and ('story' in session_id)):
#                     stream_fn = self.stream_intention_chat
#                     # 获取意图识别提示词
#                     judge_prompt, _ = self.prompts_diagrams.render_prompt(
#                         active_knowledge_contexts=None,
#                         prompt_choice=judge_make_ppt_prompt_id,
#                         user_input=prompt_data.userinput,
#                         warnings=[],
#                     )
#                     use_mcp_prompt, _ = self.prompts_diagrams.render_prompt(
#                         active_knowledge_contexts=None,
#                         prompt_choice=use_mcp_prompt_id,
#                         user_input="{user_input}",
#                         warnings=[],
#                     )
#                     # 标记类别
#                     chat_category = "boba-story"
#                     return stream_fn(
#                         basis_prompt=prompt,
#                         judge_prompt=judge_prompt,
#                         user_input=prompt_data.userinput,
#                         examine_prompt=use_mcp_prompt,
#                         chat_category=chat_category,
#                         chat_session_key_value=session_id,
#                         prompt_id=promptid,
#                         user_identifier=user_id,
#                         contexts=contexts,
#                         userContext=data.userContext,
#                         origin_url=origin_url,
#                     )
#                 return stream_fn(
#                     prompt=prompt,
#                     chat_category=chat_category,
#                     chat_session_key_value=session_id,
#                     document_keys=document,
#                     prompt_id=promptid,
#                     user_identifier=user_id,
#                     contexts=contexts,
#                     userContext=data.userContext,
#                     origin_url=origin_url,
#                 )
#
#             except Exception as error:
#                 HaivenLogger.get().error(str(error))
#                 raise HTTPException(
#                     status_code=500, detail=f"Server error: {str(error)}"
#                 )
#
#         @app.post("/api/prompt/iterate")
#         def iterate(prompt_data: IterateRequest):
#             try:
#                 if prompt_data.chatSessionId is None or prompt_data.chatSessionId == "":
#                     raise HTTPException(
#                         status_code=400, detail="chatSessionId is required"
#                     )
#                 stream_fn = self.stream_json_chat
#
#                 rendered_prompt = (
#                     f"""
#
#                     My new request:
#                     {prompt_data.userinput}
#                     """
#                     + """
#                     ### Output format: JSON with at least the "id" property repeated
#                     Here is my current working state of the data, iterate on those objects based on that request,
#                     and only return your new list of the objects in JSON format, nothing else.
#                     Be sure to repeat back to me the JSON that I already have, and only update it with my new request.
#                     Definitely repeat back to me the "id" property, so I can track your changes back to my original data.
#                     For example, if I give you
#                     [ { "title": "Paris", "id": 1 }, { "title": "London", "id": 2 } ]
#                     and ask you to add information about what you know about each of these cities, then return to me
#                     [ { "summary": "capital of France", "id": 1 }, { "summary": "Capital of the UK", "id": 2 } ]
# """
#                     + f"""
#                     ### Current JSON data
#                     {prompt_data.scenarios}
#                     Please iterate on this data based on my request. Apply my request to ALL of the objects.
#                 """
#                 )
#
#                 return stream_fn(
#                     prompt=rendered_prompt,
#                     chat_category="boba-chat",
#                     chat_session_key_value=prompt_data.chatSessionId,
#                 )
#
#             except Exception as e:
#                 raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
#
#         @app.post("/api/prompt/render")
#         @logger.catch(reraise=True)
#         def render_prompt(prompt_data: PromptRequestBody):
#             if prompt_data.promptid:
#                 prompts = (
#                     prompts_guided
#                     if prompt_data.promptid.startswith("guided-")
#                     else prompts_chat
#                 )
#
#                 rendered_prompt, template = prompts.render_prompt(
#                     active_knowledge_contexts=prompt_data.contexts,
#                     prompt_choice=prompt_data.promptid,
#                     user_input=prompt_data.userinput,
#                     additional_vars={},
#                     warnings=[],
#                     user_context=prompt_data.userContext,
#                 )
#                 return JSONResponse(
#                     {"prompt": rendered_prompt, "template": template.template}
#                 )
#             else:
#                 raise HTTPException(
#                     status_code=500, detail="Server error: promptid is required"
#                 )
#
#         @app.post("/api/prompt/image")
#         @logger.catch(reraise=True)
#         async def describe_image(prompt: str = Form(...), file: UploadFile = File(...)):
#             try:
#                 def chat_with_yield(image, prompt):
#                     for chunk in image_service.prompt_with_image(image, prompt):
#                         yield chunk
#                 file_extension = os.path.splitext(file.filename)[1].lower()
#                 contents = await file.read()
#                 if file_extension in ['.png','.jpeg','.gif','.jpg']:
#                     image = Image.open(io.BytesIO(contents))
#                 else:
#                     raise ValueError("传入图片格式有误")
#                 image_format = image.format
#                 filename = 'chat_session_key_value'+'.'+image_format
#                 # 确保临时目录存在
#                 if not os.path.exists("temp"):
#                     os.makedirs("temp")  # 使用makedirs支持递归创建目录
#                 full_path = os.path.join("temp", filename)
#                 prompt, _ = self.prompts_diagrams.render_prompt(
#                     active_knowledge_contexts=None,
#                     prompt_choice="image-description-generate",
#                     user_input="",
#                     additional_vars={"download_url":full_path},
#                     warnings=[],
#                 )
#                 image.save(full_path)
#                 return StreamingResponse(
#                     chat_with_yield(image, prompt),
#                     media_type=streaming_media_type(),
#                     headers=streaming_headers(None),
#                 )
#             except Exception as error:
#                 HaivenLogger.get().error(str(error))
#                 raise HTTPException(
#                     status_code=500, detail=f"Server error: {str(error)}"
#                 )
#
#         @app.get("/api/inspirations")
#         @logger.catch(reraise=True)
#         def get_inspirations(request: Request):
#             try:
#                 return JSONResponse(self.inspirations_manager.get_inspirations())
#             except Exception as error:
#                 HaivenLogger.get().error(str(error))
#                 raise HTTPException(
#                     status_code=500, detail=f"Server error: {str(error)}"
#                 )
#
#         @app.get("/api/inspirations/{inspiration_id}")
#         @logger.catch(reraise=True)
#         def get_inspiration_by_id(request: Request, inspiration_id: str):
#             try:
#                 inspiration = self.inspirations_manager.get_inspiration_by_id(
#                     inspiration_id
#                 )
#                 if inspiration is None:
#                     raise HTTPException(status_code=404, detail="Inspiration not found")
#                 return JSONResponse(inspiration)
#             except HTTPException:
#                 raise
#             except Exception as error:
#                 HaivenLogger.get().error(str(error))
#                 raise HTTPException(
#                     status_code=500, detail=f"Server error: {str(error)}"
#                 )
#         @app.post("/api/update/promptFile")
#         @logger.catch(reraise=True)
#         def update_prompt_file(request: Request, promptPath: str,file: UploadFile = File(...)):
#             try:
#                 path = os.path.join(config_service.load_knowledge_pack_path(), "prompts", promptPath, file.filename)
#                 if os.path.exists(path):
#                     os.remove(path)
#                 with open(path, "wb") as f:
#                     f.write(file.file.read())
#                 self.prompts_chat.reload_prompts()
#                 return JSONResponse(
#                     {"success": "true", "data": {"msg": "File uploaded successfully", "file_name": file.filename}},
#                     status_code=200
#                 )
#             except Exception as error:
#                 HaivenLogger.get().error(str(error))
#                 raise HTTPException(
#                     status_code=500, detail=f"Server error: {str(error)}"
#                 )
#
#         @app.get("/api/download/{filename}")
#         @logger.catch(reraise=True)
#         def download_file(request: Request, filename: str):
#             try:
#                 file_path = os.path.join("temp", filename)
#                 if not os.path.exists(file_path):
#                     raise HTTPException(status_code=404, detail="File not found")
#                 return FileResponse(
#                     file_path,
#                     filename=filename,
#                     media_type="application/octet-stream"
#                 )
#             except Exception as error:
#                 HaivenLogger.get().error(str(error))
#                 raise HTTPException(
#                     status_code=500, detail=f"Server error: {str(error)}"
#                 )
#
#         @app.post("/api/mermaid")
#         @logger.catch(reraise=True)
#         def mermaid_chat(request: Request, prompt_data: MermaidRequestBody):
#             origin_url = request.headers.get("referer")
#             try:
#                 stream_fn = self.stream_text_chat
#                 prompts = prompts_chat
#                 mermaid_prompt_id = os.environ.get("MERMAID_PROMPT_ID", "")
#                 user_context = prompt_data.userContext
#                 rendered_prompt, _ = prompts.render_prompt(
#                     active_knowledge_contexts=[],
#                     prompt_choice=mermaid_prompt_id,
#                     user_input=prompt_data.userinput,
#                     additional_vars={"user_context":user_context},
#                     warnings=[],
#                 )
#
#                 prompt = rendered_prompt
#                 session_id = prompt_data.chatSessionId
#
#                 return stream_fn(
#                     chat_category="boba-mermaid",
#                     chat_session_key_value=session_id,
#                     prompt=prompt
#                 )
#
#             except Exception as error:
#                 raise HTTPException(
#                     status_code=500, detail=f"Server error: {str(error)}"
#                 )
#
#         @app.post("/api/mermaidInfo")
#         @logger.catch(reraise=True)
#         def get_mermaid_image_info(request: Request,image:ImageInfoRequestBody):
#             image_id = image.imageId
#             session_id = image.sessionId
#             if image_id==None or session_id==None:
#                 return {}
#             images_info = self.chat_manager.chat_session_memory.USER_CHATS[session_id]["image"]
#             image_info = images_info[image_id]
#             return {"imageId":image_id,"userInput": image_info["image_description"], "userContext": image_info["context"],"imagePath":image_info["save_path"]}  # 返回 JSON 对象
#
#         @app.post("/api/saveImageToPPT")
#         @logger.catch(reraise=True)
#         def get_mermaid_image_info(image: UploadFile = File(...),metadata: str = Form(...)):
#             # 解析元数据
#             metadata_dict = json.loads(metadata)
#             imageId = metadata_dict["imageId"]
#             sessionId = metadata_dict["sessionId"]
#             # 设置处理过的图片
#             self.chat_manager.chat_session_memory.USER_CHATS[sessionId]["image"][imageId]["is_make"] = True
#             # 获取文件名
#             _,image_format = os.path.splitext(image.filename)
#             filename = imageId + image_format
#             # 确保临时目录存在
#             if not os.path.exists("temp"):
#                 os.makedirs("temp")
#             full_path = os.path.join("temp", filename)
#
#             # 保存图片
#             contents = image.file.read()
#             with open(full_path, "wb") as f:
#                 f.write(contents)
#             # 返回结果
#             return {
#                 "status": "success",
#             }

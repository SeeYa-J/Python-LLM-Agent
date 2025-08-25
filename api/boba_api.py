# # © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
# from fastapi import FastAPI
# from api.api_basics import ApiBasics
# from api.api_conversation import ApiConversation
# from api.api_fastapi import ApiFastAPI
# from api.api_multi_step import ApiMultiStep
# from api.api_project import ApiProject
# from api.api_scenarios import ApiScenarios
# from api.api_creative_matrix import ApiCreativeMatrix
# from api.api_company_research import ApiCompanyResearch
# from api.api_userstory import ApiUserStory
# from llms.chats import (
#     ChatManager,
# )
# from knowledge_manager import KnowledgeManager
# from llms.image_description_service import ImageDescriptionService
# from prompts.prompts_factory import PromptsFactory
# from config_service import ConfigService
# from disclaimer_and_guidelines import DisclaimerAndGuidelinesService
# from prompts.inspirations import InspirationsManager
# from utils.dependency_injection import setup_dependency_injection
#
#
# class BobaApi:
#     def __init__(
#         self,
#         prompts_factory: PromptsFactory,
#         knowledge_manager: KnowledgeManager,
#         chat_manager: ChatManager,
#         config_service: ConfigService,
#         image_service: ImageDescriptionService,
#         disclaimer_and_guidelines: DisclaimerAndGuidelinesService,
#     ):
#         # 首先初始化依赖注入容器
#         setup_dependency_injection(config_service.db_engine)
#
#         self.knowledge_manager = knowledge_manager
#         self.chat_manager = chat_manager
#         self.config_service = config_service
#         self.inspirations_manager = InspirationsManager()
#
#         self.prompts_chat = prompts_factory.create_chat_prompt_list(
#             self.knowledge_manager.knowledge_base_markdown, self.knowledge_manager
#         )
#         self.prompts_diagrams = prompts_factory.create_diagrams_prompt_list(
#             self.knowledge_manager.knowledge_base_markdown, []
#         )
#         prompts_factory_guided = PromptsFactory("./resources/prompts_guided")
#         self.prompts_guided = prompts_factory_guided.create_guided_prompt_list(
#             self.knowledge_manager.knowledge_base_markdown, self.knowledge_manager
#         )
#
#         self.model_config = self.config_service.get_chat_model()
#
#         self.image_service = image_service
#         self.disclaimer_and_guidelines = disclaimer_and_guidelines
#
#         print(f"Model used for guided mode: {self.model_config.id}")
#
#     def add_endpoints(self, app: FastAPI):
#         ApiFastAPI(
#             app
#         )
#         ApiBasics(
#             app,
#             self.chat_manager,
#             self.model_config,
#             self.prompts_guided,
#             self.knowledge_manager,
#             self.prompts_chat,
#             self.prompts_diagrams,
#             self.image_service,
#             self.config_service,
#             self.disclaimer_and_guidelines,
#             self.inspirations_manager,
#         )
#         ApiMultiStep(
#             app,
#             self.chat_manager,
#             self.model_config,
#             self.prompts_chat,
#         )
#
#         ApiScenarios(
#             app,
#             self.chat_manager,
#             self.model_config,
#             self.prompts_guided,
#         )
#         ApiCreativeMatrix(
#             app,
#             self.chat_manager,
#             self.model_config,
#             self.prompts_guided,
#         )
#
#         ApiCompanyResearch(
#             app,
#             self.chat_manager,
#             self.model_config,
#             self.prompts_guided,
#         )
#         ApiUserStory(
#             app,
#             self.chat_manager,
#             self.model_config,
#             self.prompts_guided,
#             self.config_service.db_engine,
#         )
#         ApiConversation(
#             app,
#             self.chat_manager,
#             self.model_config,
#             self.prompts_guided,
#             self.config_service.db_engine,
#         )
#         ApiProject(
#             app,
#             self.chat_manager,
#             self.model_config,
#             self.prompts_guided,
#             self.config_service.db_engine,
#         )

# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
import copy
import os
from typing import List

import yaml
from dotenv import load_dotenv
# from knowledge.pack import KnowledgePackError
# from llms.model_config import ModelConfig
# from llms.default_models import DefaultModels
# from embeddings.model import EmbeddingModel
from sqlmodel import create_engine
import re

'''
_load_yaml ：加载yaml文件，从.env中获取变量填充 yaml
_load_yaml_with_environment：加载yaml文件 及其 父yaml，调用_load_yaml进行填充
'''
class ConfigService:
    def __init__(self, environment: str = None):
        # 如果没有指定environment环境，从环境变量获取
        if environment is None:
            # 从环境变量中获取 HAIVEN_ENV的值，无则返回 dev
            environment = os.getenv('HAIVEN_ENV', 'dev')

        self.environment = environment
        self.data = self._load_yaml_with_environment(environment)
        # 加载数据库
        db_config = self.data['database']
        db_config_str = f"postgresql://{db_config['db_account']}:{db_config['db_password']}@{db_config['host']}:{db_config['port']}/{db_config['db_name']}"
        self.db_engine = create_engine(db_config_str)

    # def load_embedding_model(self) -> EmbeddingModel:
    #     """
    #     Load an embedding model from a YAML config file.
    #
    #     Args:
    #         path (str): The path to the YAML file.
    #
    #     Returns:
    #         EmbeddingModel: The loaded embedding model for the given provider
    #     """
    #
    #     default_embedding = self.load_default_models().embeddings
    #
    #     embeddings_data_list = self.data["embeddings"]
    #     embedding_model_data = next(
    #         (item for item in embeddings_data_list if item["id"] == default_embedding),
    #         None,
    #     )
    #
    #     if embedding_model_data is None:
    #         raise ValueError(f"Embeddings provider {default_embedding} not supported")
    #
    #     embedding_model = EmbeddingModel.from_dict(embedding_model_data)
    #     return embedding_model
    #
    # def load_enabled_models(self, features: List[str] = []) -> List[ModelConfig]:
    #     """
    #     Load a list of models for the enabled providers from a YAML config file.
    #
    #     Args:
    #         path (str): The path to the YAML file.
    #         features (List[str]): A list of features to filter the models by.
    #
    #     Returns:
    #         List[ModelConfig]: The loaded models.
    #     """
    #
    #     model_data_list = self.data["models"]
    #     models = []
    #
    #     for model_data in model_data_list:
    #         model = ModelConfig.from_dict(model_data)
    #         models.append(model)
    #
    #     filtered_models = copy.deepcopy(models)
    #
    #     providers = self.load_enabled_providers()
    #
    #     if providers and len(providers) > 0:
    #         filtered_models = [
    #             model
    #             for model in filtered_models
    #             if any(
    #                 model.provider.lower() == model_provider.lower()
    #                 for model_provider in providers
    #             )
    #         ]
    #
    #     if features and len(features) > 0:
    #         filtered_models = [
    #             model
    #             for model in filtered_models
    #             if all(
    #                 feature.lower()
    #                 in [model_feature.lower() for model_feature in model.features]
    #                 for feature in features
    #             )
    #         ]
    #
    #     return filtered_models
    #
    # def get_model(self, model_id: str) -> ModelConfig:
    #     """
    #     Get a model by its ID.
    #
    #     Args:
    #         model_id (str): The model ID.
    #
    #     Returns:
    #         ModelConfig: The model.
    #     """
    #     models = self.load_enabled_models()
    #     model = next((model for model in models if model.id == model_id), None)
    #
    #     if model is None:
    #         raise ValueError(f"Model with ID {model_id} not found")
    #
    #     return model
    #
    # def get_image_model(self) -> ModelConfig:
    #     available_vision_models = [
    #         (available_model.name, available_model.id)
    #         for available_model in self.load_enabled_models(
    #             features=["image-to-text"],
    #         )
    #     ]
    #
    #     image_model_id = (
    #         self.load_default_models().vision or available_vision_models[0][1]
    #         if len(available_vision_models) > 0
    #         else None
    #     )
    #
    #     return self.get_model(image_model_id)
    #
    # def get_chat_model(self) -> ModelConfig:
    #     available_chat_models = [
    #         (available_model.name, available_model.id)
    #         for available_model in self.load_enabled_models(
    #             features=["text-generation"],
    #         )
    #     ]
    #
    #     chat_model_id = (
    #         self.load_default_models().chat or self.get_default_chat_model()
    #         if len(available_chat_models) > 0
    #         else None
    #     )
    #
    #     return self.get_model(chat_model_id)
    #
    # def load_knowledge_pack_path(self) -> str:
    #     """
    #     Load the knowledge pack path from a YAML config file.
    #
    #     Args:
    #         config_file_path (str): The path to the YAML file.
    #
    #     Returns:
    #         str: The knowledge pack path.
    #     """
    #     knowledge_pack_path = self.data["knowledge_pack_path"]
    #
    #     if not os.path.exists(knowledge_pack_path):
    #         raise KnowledgePackError(
    #             f"Cannot find path to Knowledge Pack: `{knowledge_pack_path}`. Please check the `knowledge_pack_path` in your config file."
    #         )
    #
    #     return knowledge_pack_path
    #
    # def load_enabled_providers(self) -> List[str]:
    #     """
    #     Load the enabled providers from the specified YAML configuration file.
    #
    #     Args:
    #         path (str, optional): The path to the YAML configuration file. Defaults to "config.yaml".
    #
    #     Returns:
    #         List[str]: The list of enabled providers.
    #
    #     """
    #
    #     enabled_providers = self.data["enabled_providers"]
    #
    #     if isinstance(enabled_providers, str):
    #         enabled_providers = enabled_providers.split(",")
    #
    #     return enabled_providers
    #
    # def load_default_models(self) -> DefaultModels:
    #     """
    #     Load the default models from a YAML file.
    #
    #     Args:
    #         path (str): The path to the YAML file. Defaults to "config.yaml".
    #
    #     Returns:
    #         DefaultModels: An instance of the DefaultModels config class containing the default model set for llm, vision and embeddings.
    #
    #     """
    #     default_models = DefaultModels.from_dict(self.data["default_models"])
    #
    #     return default_models
    #
    # def get_default_chat_model(self) -> str:
    #     """
    #     Get the default chat model from the config file.
    #
    #     Args:
    #         path (str): The path to the YAML file.
    #
    #     Returns:
    #         str: The default chat model.
    #     """
    #     default_chat_model = self.load_default_models().chat
    #     if default_chat_model is None or default_chat_model == "":
    #         enabled_provider = self.load_enabled_providers()[0]
    #         match enabled_provider:
    #             case "OPENAI":
    #                 default_chat_model = "openai-gpt-4o"
    #             case "azure":
    #                 default_chat_model = "azure-gpt-4o"
    #             case "gcp":
    #                 default_chat_model = "google-gemini"
    #             case "aws":
    #                 default_chat_model = "aws-claude-sonnet-3.7"
    #             case "anthropic":
    #                 default_chat_model = "anthropic-claude-3.7"
    #             case "ollama":
    #                 default_chat_model = "ollama-local-llama3"
    #     return default_chat_model

    def _load_yaml(self, path: str) -> dict:
        """
        Load YAML data from a config file.
        加载Yaml，保留时间戳为字符串，并用.env填充占位符
        Args:
            path (str): The path to the YAML file.

        Returns:
            dict: The loaded YAML data.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path {path} is not valid")

        data = None

        # 使用自定义构造器_string_constructor，禁用了默认YAML时间戳到datetime对象的自动转换
        yaml.SafeLoader.add_constructor(
            "tag:yaml.org,2002:timestamp", ConfigService._string_constructor
        )

        with open(path, "r", encoding="utf8") as file:
            try:
                data = yaml.load(file, Loader=yaml.SafeLoader)
                # data就是yaml文件解析出来的dict
            except yaml.YAMLError as exc:
                print(exc)

        return _resolve_config_values(data)

    def _load_yaml_with_environment(self, environment: str):
        """
        加载环境特定的配置文件
        _load
        Args:
            environment (str): 环境名称 (dev/test/prod)
        Returns:
            dict: 合并后的配置数据
        """
        # 首先尝试加载环境特定的配置文件
        env_config_path = f"config/{environment}.yaml"

        # 加载环境配置
        env_data = self._load_yaml(env_config_path)

        # 如果环境配置继承了基础配置
        if 'extends' in env_data:
            base_config_path = f"config/{env_data['extends']}"
            if os.path.exists(base_config_path):
                base_data = self._load_yaml(base_config_path)
                # 合并yaml及其父yaml配置，环境配置覆盖基础配置
                merged_data = self._merge_configs(base_data, env_data)
                return merged_data
        return env_data

    def _merge_configs(self, base_config: dict, env_config: dict) -> dict:
        """
        合并基础配置和环境配置

        Args:
            base_config (dict): 基础配置
            env_config (dict): 环境配置

        Returns:
            dict: 合并后的配置
        """
        merged = copy.deepcopy(base_config)

        for key, value in env_config.items():
            if key == 'extends':
                continue  # 跳过extends字段

            if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                # 递归合并字典
                merged[key] = self._merge_configs(merged[key], value)
            else:
                # 直接覆盖
                merged[key] = value

        return merged

    @staticmethod
    def _string_constructor(loader, node):
        """
        Custom constructor for handling YAML strings.
        直接提取节点的原始字符串值
        Args:
            loader: The YAML loader.YAML解析器实例
            node: The YAML node.YAML文档中代表时间戳的节点。

        Returns:
            str: The constructed string.
        """
        return loader.construct_scalar(node)

    def get_environment(self) -> str:
        """获取当前环境"""
        return self.environment

    def is_development(self) -> bool:
        """检查是否为开发环境"""
        return self.environment == 'dev'

    def is_testing(self) -> bool:
        """检查是否为测试环境"""
        return self.environment == 'test'

    def is_production(self) -> bool:
        """检查是否为生产环境"""
        return self.environment == 'prod'


def _resolve_config_values(config: dict[str, str]):
    '''
    input：yaml.load文件
    outPut：根据本地环境，填充好的input
    '''
    load_dotenv() # 加载.env文件中的环境变量
    for key, value in config.items():
        if isinstance(value, dict): # 处理子配置
            _resolve_config_values(value)
        elif isinstance(value, list): #处理列表元素
            _resolve_config_list_values(config, key, value)
        else: #处理基本元素
            config[key] = _replace_by_env_var(config[key])
            if _is_comma_separated_list(config[key]):
                config[key] = config[key].split(",")

    return config


def _is_comma_separated_list(value: str) -> bool:
    return isinstance(value, str) and "," in value


def _resolve_config_list_values(config, key, value):
    list = []
    for i, item in enumerate(value):
        if isinstance(item, dict):
            list.append(_resolve_config_values(item))
        else:
            list.append(_replace_by_env_var(item))

    config[key] = list


def _replace_by_env_var(value):
    if value is None:
        return value

    # 只处理字符串类型，其他类型直接返回
    if not isinstance(value, str):
        return value

    # 使用 regex 查找所有 ${ENV_VAR} 模式，并替换为其值
    def replace_env_var(match):
        env_variable = match.group(1) # match.group(1)获取 VAR_NAME,group(0)是${VAR_NAME}
        return os.environ.get(env_variable, "")

    # 使用正则表达式r"\${([^}]+)}"来查找字符串中所有的${VAR_NAME}形式的占位符，并对每个匹配调用
    # re.sub(pattern：表示正则中的模式字符串,repl：表示要替换的字符串(可是函数），string：要被处理的原始字符串；
    # \$ 转义$ , ([^}]+) 匹配1个或多个非}字符
    return re.sub(r"\${([^}]+)}", replace_env_var, value)

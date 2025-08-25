# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
from typing import Type, Dict, get_type_hints, Union, Set,Any
from logger import HaivenLogger
from dao.base_dao import BaseDAO


class DIContainer:
    """依赖注入容器 - 两阶段初始化单例模式"""

    _instance = None
    _db_engine = None # 数据库
    _registered_classes: Set[Type] = set()  # 已注册的类
    _bean_instances: Dict[Type, Any] = {}  # 类到实例的直接映射
    _initialized: bool = False  # 是否已经完成依赖注入初始化

    def __new__(cls): # 实现单例模式，确保一个类只有一个实例。
        if cls._instance is None:
            cls._instance = super(DIContainer, cls).__new__(cls)
            cls._registered_classes = set()
            cls._bean_instances = {}
            cls._initialized = False
        return cls._instance

    @classmethod
    def initialize(cls, db_engine):
        """初始化容器"""
        cls._db_engine = db_engine
        cls._instance = cls()
        # 立即执行两阶段初始化
        cls._instance._initialize_beans()
        return cls._instance

    def _initialize_beans(self):
        """ 两阶段初始化：先创建所有bean，再注入依赖 """
        if self._initialized:
            return
        
        # 阶段一：创建所有注册类的实例
        HaivenLogger.get().info("DI containder: bean initialization phase 1: creating all Bean instances")
        for bean_class in self._registered_classes:
            self._create_bean_instance(bean_class)

        # 阶段二：为所有实例注入依赖
        HaivenLogger.get().info("DI containder: bean initialization phase 2: injecting dependencies")
        for bean_class, instance in self._bean_instances.items():
            self._inject_dependencies(instance)

        self._initialized = True
        HaivenLogger.get().info(f"DI containder: all beans initialized successfully, total {len(self._bean_instances)} beans")

    def _create_bean_instance(self, bean_class: Type) -> Any:
        """创建bean实例，但不注入依赖"""
        if bean_class in self._bean_instances: # 已注册，直接返回
            return self._bean_instances[bean_class]

        # 创建实例
        try: # hasattr(object, name) 检测 object是否含有name属性
            if hasattr(bean_class, "__subclasses__") and issubclass(bean_class, BaseDAO):
                # DAO需要db_engine参数
                instance = bean_class(self._db_engine)
            else:
                # Service和Controller不需要参数
                instance = bean_class()

            # 存储实例
            self._bean_instances[bean_class] = instance
            return instance
        except Exception as e:
            HaivenLogger.get().error(f"Bean create field {bean_class.__name__}: {str(e)}")
            raise

    def _inject_dependencies(self, instance):
        """为实例注入依赖"""
        # 获取类的类型注解，（如：service: UserService）
        type_hints = get_type_hints(type(instance))

        for attr_name, dependency_type in type_hints.items():
            # 跳过非依赖注入的属性
            if attr_name.startswith('_') or attr_name in ['return']:
                continue

            # 检查是否已经有值，getattr(instance, attr_name) 获取instance.attr_name的值
            if hasattr(instance, attr_name) and getattr(instance, attr_name) is not None:
                continue

            # 检查是否是注册的组件类型
            if dependency_type in self._registered_classes:
                # 依赖类必须已经在容器中
                if dependency_type not in self._bean_instances:
                    raise ValueError(f"dependency {dependency_type.__name__} not found in DI container. Did you forget to register it?")

                # 直接获取已创建的实例
                dependency_instance = self._bean_instances[dependency_type]

                # 设置属性
                setattr(instance, attr_name, dependency_instance)


    @classmethod
    def register_component(cls, component_class: Type):
        """注册组件到容器"""
        cls._registered_classes.add(component_class)
        HaivenLogger.get().info(f"Registered component: {component_class.__name__}")

    @classmethod
    def register_obj(cls, key: Type, value: Any):
        """注册对象到容器, kay为类对象，value为已经实例化的对象"""
        if not isinstance(key, type):
            raise TypeError("Key must be a class type")
        if key in cls._bean_instances:
            raise ValueError(f"Component {key.__name__} already registered.")
        cls._bean_instances[key] = value
        cls._registered_classes.add(key)
        HaivenLogger.get().info(f"Registered object: {key.__name__}")

    def get_bean(self, bean_class: Type) -> Any:
        """获取Bean实例"""
        # 如果尚未初始化，则执行初始化
        if not self._initialized:
            self._initialize_beans()

        if bean_class not in self._registered_classes:
            raise ValueError(f"Component {bean_class.__name__} not registered. Did you forget @component, @service, or @repository?")

        if bean_class not in self._bean_instances:
            raise ValueError(f"Component {bean_class.__name__} is registered but instance not found.")

        return self._bean_instances[bean_class]

    @classmethod
    def clear(cls):
        """清理容器（主要用于测试）"""
        cls._bean_instances.clear()
        cls._registered_classes.clear()
        cls._initialized = False


# 全局容器实例
_container = None


def get_container() -> DIContainer:
    """获取全局容器实例"""
    global _container
    if _container is None:
        _container = DIContainer()
    return _container


def component(cls):
    """
    组件装饰器 - 只支持 @component 用法
    """
    container = get_container()
    container.register_component(cls)
    return cls


def service(cls):
    """
    服务装饰器 - 只支持 @service 用法
    """
    return component(cls)


def repository(cls):
    """
    仓库装饰器 - 只支持 @repository 用法
    """
    return component(cls)


def controller(cls):
    """
    控制器装饰器 - 只支持 @controller 用法
    """
    return component(cls)


# 用于初始化DI容器的函数
def setup_dependency_injection(db_engine):
    """设置依赖注入容器"""
    global _container
    _container = DIContainer.initialize(db_engine)

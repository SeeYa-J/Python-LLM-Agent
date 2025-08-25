# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
import json
import sys
from loguru import logger #日志记录库


class HaivenLogger:
    __instance = None # 现单例模式，确保全局唯一实例
    def __init__(self, loguru_logger):
        print("instantiating HaivenLogger")
        loguru_logger.remove() # 清除默认日志处理器

        self.logger = loguru_logger.patch(HaivenLogger.patching)# 添加 补丁
        self.logger.add(sys.stdout, format="{extra[serialized]}")# 添加标准输出处理器，sys.stdout输出到控制台

        self.logger.level("ANALYTICS", no=60)# 创建新日志级别"ANALYTICS"，60级，高于默认的WARNING

        if HaivenLogger.__instance is not None:
            raise Exception(
                "HaivenLogger is a singleton class. Use getInstance() to get the instance."
            )
        HaivenLogger.__instance = self #设置为当前实例

    # 以下日志分析方法
    def analytics(self, message, extra=None): # 业务分析专用
        self.logger.log("ANALYTICS", message, extra=extra)

    def error(self, message, extra=None): # 错误日志
        self.logger.error(message, extra=extra)

    def info(self, message, extra=None): # 信息日志
        self.logger.info(message, extra=extra)

    def warn(self, message, extra=None): # 警告日志
        self.logger.warning(message, extra=extra)

    @staticmethod
    def get(): # 单例访问点
        if HaivenLogger.__instance is None:
            HaivenLogger(logger)
        return HaivenLogger.__instance

    @staticmethod # staticmethod可以 类名.静态方法、实例.静态方法
    def serialize(record): # 日志结构化方法
        subset = {
            "time": str(record["time"]),
            "message": record["message"],
            "level": record["level"].name,
            "file": record["file"].path,
        }
        subset.update(record["extra"])
        return json.dumps(subset)

    @staticmethod
    def patching(record): # 日志补丁函数
        record["extra"]["serialized"] = HaivenLogger.serialize(record)

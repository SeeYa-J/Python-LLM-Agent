# © 2024 Thoughtworks, Inc. | Licensed under the Apache License, Version 2.0  | See LICENSE.md file for permissions.
import json
import sys
from loguru import logger


class HaivenLogger:
    __instance = None

    def __init__(self, loguru_logger):
        print("instantiating HaivenLogger")
        loguru_logger.remove()

        self.logger = loguru_logger.patch(HaivenLogger.patching)
        self.logger.add(sys.stdout, format="{extra[serialized]}")

        self.logger.level("ANALYTICS", no=60)

        if HaivenLogger.__instance is not None:
            raise Exception(
                "HaivenLogger is a singleton class. Use getInstance() to get the instance."
            )
        HaivenLogger.__instance = self

    def analytics(self, message, extra=None):
        self.logger.log("ANALYTICS", message, extra=extra)

    def error(self, message, extra=None):
        self.logger.error(message, extra=extra)

    def info(self, message, extra=None):
        self.logger.info(message, extra=extra)

    def warn(self, message, extra=None):
        self.logger.warning(message, extra=extra)

    @staticmethod
    def get():
        if HaivenLogger.__instance is None:
            HaivenLogger(logger)
        return HaivenLogger.__instance

    @staticmethod
    def serialize(record):
        subset = {
            "time": str(record["time"]),
            "message": record["message"],
            "level": record["level"].name,
            "file": record["file"].path,
        }
        subset.update(record["extra"])
        return json.dumps(subset,ensure_ascii=False)

    @staticmethod
    def patching(record):
        record["extra"]["serialized"] = HaivenLogger.serialize(record)

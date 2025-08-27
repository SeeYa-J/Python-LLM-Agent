import random
import string
import traceback
import requests
import time
import json
import uuid
import re
from config.constants import THINK_NOTE1, THINK_NOTE2

class AiforceUtil:
    tokenMap = {}
    CONFIG = {
        "api_key": "M/+jhoQ6UXZxU86ZTFxaygoN1ZJtKXXG",
        "secret_key": "JLpygYJYrKEZkGzC1uHIusKj/CJ5AXII",
        "service_id": {
            "invoice_ocr": "1871080863769427968",
            "code_reader": "1901519946683047936",
            "doc_editor": "1907617846361554944",
            "shenhaotest": "1914220940003061760",
            "baosongtest": "1849753300972187648",
            "TEST":"1849753300972187648"
        },
        "user_code": "POCM",
        "token_url": "https://aiforceplatformfeuat.t-sy-in.earth.xcloud.lenovo.com/aiforceplatformapi/openapi/oauth/token/get",
        "llm_url": "https://aiforceplatformfeuat.t-sy-in.earth.xcloud.lenovo.com/aiforceplatformapi/openapi/llm/debugSse"
    }
    @staticmethod
    def set_config(config):
        AiforceUtil.CONFIG=config

    @staticmethod
    def get_new_token(service_name: str):
        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        request_data = {
            "apiKey": AiforceUtil.CONFIG['api_key'],
            "secretKey": AiforceUtil.CONFIG['secret_key'],
            "requestTime": int(time.time() * 1000),
            "serviceId": service_name,
        }
        response = requests.post(json=request_data, url=AiforceUtil.CONFIG['token_url'], headers=headers, verify=False)
        # sample: {'code': 200, 'msg': '处理成功', 'time': 1734579104190, 'data': {'refreshToken': '123', 'accessToken': '123', 'userCode': 'guish2', 'expiresAt': '2024-12-26 11:31:44', 'expiresIn': 604800}}
        response = response.json()
        if response.get('code') == 200:
            data = response.get('data')
            if AiforceUtil.tokenMap.get(service_name) is None:
                AiforceUtil.tokenMap[service_name] = {}
            AiforceUtil.tokenMap[service_name]['accessToken'] = data.get('accessToken')
            AiforceUtil.tokenMap[service_name]['expiresAt'] = data.get('expiresAt')
            return data.get('accessToken')
        else:
            return "error"

    @staticmethod
    def get_token(service_id: str):
        if AiforceUtil.tokenMap.get(service_id) is None or AiforceUtil.tokenMap.get(service_id).get('expiresAt') < time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()):
            AiforceUtil.get_new_token(service_id)
        return AiforceUtil.tokenMap.get(service_id).get('accessToken')

    @staticmethod
    def send_request(llm_input: str, service_id: str, session_id: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "OpenApiDoorKey": AiforceUtil.get_token(service_id)
        }
        random_int = random.randint(3, 8)
        letters = string.ascii_letters
        user_code = ''.join(random.choice(letters) for _ in range(random_int))
        request_data = {
            "userInput": llm_input,
            "sessionId": session_id[:50],  # aiforce限制长度50以内
            "serviceId": service_id,
            "requestId": str(uuid.uuid4()),
            "userCode": user_code,
        }
        res = ""
        response = requests.post(json=request_data, url=AiforceUtil.CONFIG["llm_url"], headers=headers, verify=False,
                                 stream=True)
        try:
            temp_data = ""
            thinking = False
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_data += chunk.decode('utf-8')
                    if temp_data.endswith("\n\n"):
                        lines = temp_data.split('\n')
                        outer_data = lines[1].split(":", 1)[1]  # 从第二行开始是数据, TODO: 这里可能会报错
                        if "data" in outer_data:
                            inner_data_dict = json.loads(outer_data)
                            inner_data = inner_data_dict.get('data')
                            if inner_data:  # 确保非null
                                if thinking:
                                    thinking = False
                                    yield THINK_NOTE2
                                yield inner_data
                        elif "think" in outer_data:
                            inner_data_dict = json.loads(outer_data)
                            inner_data = inner_data_dict.get('think')
                            if inner_data:
                                if not thinking:
                                    thinking = True
                                    yield THINK_NOTE1
                                yield inner_data
                        elif "warning" in outer_data:
                            msg = json.loads(outer_data).get('warning')
                            yield msg
                        elif "referenceInfo" in outer_data:
                            msg = json.loads(outer_data).get('referenceInfo')
                            yield msg
                        temp_data = ""
        except Exception as e:
            yield "error in line: " + str(e.__traceback__.tb_lineno) + "; \nError msg: " + traceback.format_exc()

    @staticmethod
    def chat(llm_input: str, service_id: str, session_id: str):
        buffer = ""
        for chunk in AiforceUtil.send_request(llm_input, service_id, session_id):
            if '`' in chunk:
                buffer += re.sub(r'\s+', '', chunk)
            elif buffer:
                yield buffer
                buffer = ""
                yield chunk
            else:
                yield chunk
    @staticmethod
    def get_all_result(llm_input: str, service_id: str, session_id: str):
        buffer = ""
        for chunk in AiforceUtil.send_request(llm_input, service_id, session_id):
            buffer+=chunk
        return buffer

if __name__ == '__main__':
    for char in AiforceUtil.chat("你好", "baosongtest", "1234"):
        print(char)
    print(uuid.uuid4())
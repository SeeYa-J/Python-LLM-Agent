import random
import string
import traceback
import requests
import time
import json
import uuid
import re
from config.constants import THINK_NOTE1, THINK_NOTE2
'''
AI 服务调用的核心工具类，通过发送request请求,与AI Force 平台交互
'''
class AiforceUtil:
    tokenMap = {} # 用于缓存不同服务的token
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
        # sample: {'code': 200, 'msg': '处理成功', 'time': 1734579104190
        # , 'data': {'refreshToken': '123', 'accessToken': '123', 'userCode': 'guish2', 'expiresAt': '2024-12-26 11:31:44', 'expiresIn': 604800}}
        response = response.json()
        if response.get('code') == 200:
            data = response.get('data')
            # 将token缓存到tokenMap中
            if AiforceUtil.tokenMap.get(service_name) is None:
                AiforceUtil.tokenMap[service_name] = {}
            AiforceUtil.tokenMap[service_name]['accessToken'] = data.get('accessToken')
            AiforceUtil.tokenMap[service_name]['expiresAt'] = data.get('expiresAt')
            return data.get('accessToken')
        else:
            return "error"

    @staticmethod
    def get_token(service_id: str):
        # 检查缓存中是否有该服务的token，且是否过期（通过比较当前时间和过期时间）
        # 过期重新获取，未过期从tokenMap中获取
        if AiforceUtil.tokenMap.get(service_id) is None or AiforceUtil.tokenMap.get(service_id).get('expiresAt') < time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()):
            AiforceUtil.get_new_token(service_id)
        return AiforceUtil.tokenMap.get(service_id).get('accessToken')


    @staticmethod ### 通过request（stream=True)，yield 实现流式输出
    def send_request(llm_input: str, service_id: str, session_id: str) -> str:

        ### 流式请求处理 (send_request)
        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "OpenApiDoorKey": AiforceUtil.get_token(service_id)
        }
        random_int = random.randint(3, 8)# 生成介于3~8间的随机整数
        letters = string.ascii_letters # 所有的 ASCII 字母字符
        ## 生成随机user_code
        user_code = ''.join(random.choice(letters) for _ in range(random_int))
        request_data = {
            "userInput": llm_input,
            "sessionId": session_id[:50],  # aiforce限制长度50以内
            "serviceId": service_id,
            "requestId": str(uuid.uuid4()),
            "userCode": user_code,
        }
        res = ""
        ## stream=True——》流式请求，
        response = requests.post(json=request_data
                                 , url=AiforceUtil.CONFIG["llm_url"]
                                 , headers=headers, verify=False,
                                 stream=True)
        try:
            temp_data = ""
            thinking = False
            # 逐chunk读取内容
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_data += chunk.decode('utf-8')
                    if temp_data.endswith("\n\n"): # 消息结束标识符
                        lines = temp_data.split('\n') # 按行分割
                        outer_data = lines[1].split(":", 1)[1]  # 从第二行开始是数据, TODO: 这里可能会报错
                        if "data" in outer_data: #加载Data
                            inner_data_dict = json.loads(outer_data)
                            inner_data = inner_data_dict.get('data')
                            if inner_data:  # 确保data非null
                                if thinking:# 存在think头
                                    thinking = False
                                    yield THINK_NOTE2 #</think>尾标识
                                yield inner_data # yield返回的是个迭代器
                        elif "think" in outer_data:# 加载think
                            inner_data_dict = json.loads(outer_data)
                            inner_data = inner_data_dict.get('think')
                            if inner_data:
                                if not thinking: # 无think头，添加think头
                                    thinking = True
                                    yield THINK_NOTE1 # <think> 首标识
                                yield inner_data
                        elif "warning" in outer_data:# 输出warning
                            msg = json.loads(outer_data).get('warning')
                            yield msg
                        elif "referenceInfo" in outer_data:# 输出referenceInfo
                            msg = json.loads(outer_data).get('referenceInfo')
                            yield msg
                        temp_data = ""
        except Exception as e:
            yield "error in line: " + str(e.__traceback__.tb_lineno) + "; \nError msg: " + traceback.format_exc()

    @staticmethod ## 输出 send_request
    def chat(llm_input: str, service_id: str, session_id: str):
        buffer = ""
        for chunk in AiforceUtil.send_request(llm_input, service_id, session_id):
            if '`' in chunk:
                ## sub正则替换，用‘’ 替换 \s匹配任意空白字符（空格、制表符 \t、换行符 \n、回车符 \r）
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
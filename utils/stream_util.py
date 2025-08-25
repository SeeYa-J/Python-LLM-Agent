import asyncio
import copy
import os
import uuid

from config.constants import FILE_NOTE1, FILE_NOTE2
from llms.aiforce_util import AiforceUtil
import re

from utils.PDFUtils import PPTUtil
from utils.mcp_util.mcp_client import MCPClient


class StreamUtil:
    special_data = {'csv','ppt','json','mermaid'}
    # 基础的流处理-截取特殊消息返回chunk
    @staticmethod
    def stream_basis(model_config,query,service_name, chat_session_key_value,special_msg):
        is_in_special = False  # 标记此时是否处于特殊数据块
        special_flag = {}  # 记录下代码块内容
        buffer = ""
        # 切换agent
        AiforceUtil.set_config(model_config)
        for chunk in AiforceUtil.chat(query, service_name, chat_session_key_value):
            # 判断特殊消息是否出现
            if not is_in_special:
                # 使用正则表达式查找匹配位置
                for flag in StreamUtil.special_data:
                    match = re.search(fr'</think>\s*```\s*{flag}', buffer)
                    if match:
                        special_flag[flag] = True
            # special_msg 截获区
            for key in special_flag.keys():
                if special_flag[key]:
                    if key not in special_msg:  # 当前的chunk是key名称，忽略掉，同时初始化
                        special_msg[key] = ""
                    else:
                        special_msg[key] += chunk
            buffer += chunk
            yield chunk
        if buffer == "":
            # 抛出AIFORCE无返回值异常
            raise ValueError("AIFORCE返回内容失败，请重新尝试")

    # 生成PPT流处理函数
    @staticmethod
    def stream_ppt(model_config,chat_session_key_value, prompt,make_flag,user_input,user_ppt_data,is_examine,examine_ppt_prompt):
        try:
            special_msg = {}
            ppt_flag = False
            if not make_flag:
                for chunk in StreamUtil.stream_basis(model_config["agent-supply-chain"],prompt,"1849753300972187648",chat_session_key_value,special_msg):
                    # 特殊数据不立即返回
                    if not ppt_flag:
                        if "ppt" in special_msg:
                            ppt_flag = True
                        yield chunk
                # 处理特殊消息
                for key in special_msg.keys():
                    if key == 'ppt':
                        if is_examine:
                            # 输出质量检查
                            ppt_scheme = special_msg[key]
                            # 切换agent
                            AiforceUtil.set_config(model_config["agent-supply-chain"])
                            update_ppt_scheme = ""
                            for chunk in PPTUtil.examine_ppt_scheme_use_ai(ppt_scheme, examine_ppt_prompt, "1849753300972187648"):
                                update_ppt_scheme += chunk
                                yield chunk
                            special_msg[key] = update_ppt_scheme
                        # 生成结束符号
                        yield "\n```\n"
                        # 解析PPT制作方案中需要生成的图片的相关信息保存至user_ppt_data["image"]，并且将图片下载路径替换成真实路径返回修改后的PPT制作方案
                        new_ppt_txt, have_image = PPTUtil.parse_image(special_msg[key], user_ppt_data["image"],
                                                                      user_input)
                        # 保存处理后的PPT制作方案
                        user_ppt_data["last_ppt_scheme"] = new_ppt_txt
                        if have_image:
                            # 生成mermaid制作链接
                            yield "请点击如下链接制作mermaid图片：\n<table>"
                            i = 1
                            for key, value in user_ppt_data["image"].items():
                                if not value["is_make"]:
                                    image_des = value["image_description"]
                                    localHost = os.environ.get("SMERMAID_URL", "")
                                    mermaid_url = localHost + "/?image_id=" + key + "&" + "session_id=" + chat_session_key_value
                                    yield "<table-head>图片序号</table-head>：" + "<table-data>" + str(
                                        i) + "</table-data>" + ";" + "<table-head>图片描述</table-head>：" + "<table-data>" + image_des + "</table-data>" + ";" + "<table-head>mermaid制作链接</table-head>:" + "<table-data>" + mermaid_url + "</table-data>" + "\n"
                                    i += 1
                                    value["is_make"] = True
                            yield "</table>"
                        yield "如果对当前制作的ppt不满意用户可以继续提要求修改ppt，如果满意即可开始ppt的制作"
            else:
                # 获取用户满意的PPT制作方案
                last_scheme = user_ppt_data["last_ppt_scheme"]
                # 获取结构化信息
                ppt_info = PPTUtil.get_ppt_info(last_scheme)
                # 根据结构化信息制作PPT
                prs = PPTUtil.get_ppt_file(ppt_info)
                filename = "{}.pptx".format(chat_session_key_value)
                # 确保临时目录存在
                if not os.path.exists("temp"):
                    os.makedirs("temp")  # 使用makedirs支持递归创建目录
                # 保存PPTX文件
                full_path = os.path.join("temp", filename)
                PPTUtil.save_ppt(prs, full_path)
                # 生成下载链接
                file_info = FILE_NOTE1 + os.getenv("BASE_URL",
                                                   "http://localhost:8080") + "/api/download/" + filename + FILE_NOTE2
                for char in file_info:
                    yield char
        except Exception as error:
            if not str(error).strip():
                error = "Error while the model was processing the input"
            print(f"[ERROR]: {str(error)}")
            yield f"[ERROR]: {str(error)}"

    # 直连AI VERSE解析图片
    @staticmethod
    def stream_image(image, prompt,image_service):
        try:
            for chunk in image_service.prompt_with_image(image, prompt):
                yield chunk
        except Exception as error:
            if not str(error).strip():
                error = "Error while the model was processing the input"
            print(f"[ERROR]: {str(error)}")
            yield f"[ERROR]: {str(error)}"

    # 纯文本流处理函数
    @staticmethod
    def stream_text(model_config,chat_session_key_value, prompt,outer_special_msg=None):
        try:
            special_msg = {}
            for chunk in StreamUtil.stream_basis(model_config["agent-supply-chain"], prompt, "1849753300972187648",chat_session_key_value, special_msg):
                yield chunk
            # 处理特殊消息
            for chunk in StreamUtil.process_csv_msg(special_msg,chat_session_key_value):
                yield chunk
        except Exception as error:
            if not str(error).strip():
                error = "Error while the model was processing the input"
            print(f"[ERROR]: {str(error)}")
            yield f"[ERROR]: {str(error)}"

    # mermaid流处理函数
    @staticmethod
    def stream_mermaid(model_config,chat_session_key_value, prompt):
        try:
            special_msg = {}
            buffer = ""
            for chunk in StreamUtil.stream_basis(model_config["agent-supply-chain"], prompt, "1849753300972187648",chat_session_key_value, special_msg):
                buffer += chunk
            # 处理特殊消息
            for key in special_msg.keys():
                # if special_flag[key]:
                if key == "mermaid":
                    yield special_msg["mermaid"]
        except Exception as error:
            if not str(error).strip():
                error = "Error while the model was processing the input"
            print(f"[ERROR]: {str(error)}")
            yield f"[ERROR]: {str(error)}"

    # userStory流处理函数
    @staticmethod
    def stream_user_story(chat_session_key_value, prompt, query_prompt, model_config, make_flag,
                          user_story_data, project_name):
        # 处理csv文本数据
        def csv_to_dict(csv_string):
            # 分割 CSV 字符串为行
            lines = csv_string.strip().split('\n')

            # 设置标题行
            headers = ["Summary", "Background", "Description", "Acceptance Criteria", "Story Points", "Priority","planned start","planned end"]
            result = []
            # 处理每一行数据
            for line in lines[1:]:
                # 处理引号包含的逗号
                values = []
                current_value = ''
                in_quotes = False

                for char in line:
                    if char == '"':
                        in_quotes = not in_quotes
                    elif char == ',' and not in_quotes:
                        values.append(current_value.strip('"'))
                        current_value = ''
                    else:
                        current_value += char

                # 添加最后一个值
                values.append(current_value.strip('"'))

                # 创建字典
                item = {}
                for i in range(len(headers)):
                    # 加入测试标签
                    if headers[i]=="Summary":
                        values[i] = "AI-TEST-"+values[i]
                    if headers[i]=="planned start":
                        item[headers[i].strip()] = "2025-07-04T23:37:00.000+0800"
                    elif headers[i]=="planned end":
                        item[headers[i].strip()] = "2025-010-04T23:37:00.000+0800"
                    else:
                        item[headers[i].strip()] = values[i].strip()
                result.append(item)

            return result
        client = MCPClient()
        loop = None
        try:
            # 创建单个事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            if not make_flag:
                special_msg = {}
                for chunk in StreamUtil.stream_basis(model_config["agent-supply-chain"], prompt, "1849753300972187648",
                                                     chat_session_key_value, special_msg):
                    yield chunk
                # 处理特殊消息
                for chunk in StreamUtil.process_csv_msg(special_msg, chat_session_key_value, user_story_data):
                    yield chunk
                yield "\n如果对当前user story不满意用户可以继续提要求修改user story，如果满意即可开始导入JIRA"
            else:
                # 解析用户故事
                user_story = csv_to_dict(user_story_data["last_user_story_scheme"])
                for i in range(len(user_story)):
                    # 防止身份验证超时
                    loop.run_until_complete(client.connect_to_server())
                    user_input = f"帮我把下列以给出的用户故事Issue type以story的形式插入JIRA中的{project_name}项目中：" + str(
                        user_story[i])
                    user_input = query_prompt.format(user_input=user_input)

                    response = loop.run_until_complete(client.process_query(user_input))
                    yield response
        finally:
            if loop:
                # 确保所有任务完成后关闭循环
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                loop.close()
            client.cleanup()
    # 处理csv特殊消息
    @staticmethod
    def process_csv_msg(special_msg,chat_session_key_value,user_story_data=None):
        for key in special_msg.keys():
            # if special_flag[key]:
            if key == "csv":
                # 保存csv
                if user_story_data:
                    user_story_data["last_user_story_scheme"] = special_msg[key]
                csv_msg = special_msg[key].lstrip('\n')
                filename = "{}.csv".format(chat_session_key_value)
                if not os.path.exists("temp"):
                    os.mkdir("temp")
                with open(os.path.join("temp", filename), "w", encoding='utf-8-sig') as f:
                    f.write(csv_msg)
                # 输出csv的下载链接
                file_info = FILE_NOTE1 + os.getenv("BASE_URL",
                                                   "http://localhost:8080") + "/api/download/" + filename + FILE_NOTE2
                for char in file_info:
                    yield char

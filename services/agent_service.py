import io
import re
from typing import NotRequired, Optional
import json
from langchain_core.messages import AIMessageChunk, AIMessage
from langchain_deepseek import ChatDeepSeek
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.config import get_stream_writer
from langgraph.constants import START, END
from langgraph.graph import StateGraph, MessagesState
from psycopg_pool import ConnectionPool

from config_service import ConfigService
from logger import HaivenLogger
from services.conversation_service import ConversationService
from services.prompt_service import PromptService
from services.user_story_service import UserStoryService
from utils.apih_util import ApihUtil
from utils.dependency_injection import service, get_container
from utils.kmverse_util import KmverseUtil
from utils.response_utils import ApiResponse
from PIL import Image
import io
from urllib.parse import quote_plus

class State(MessagesState):
    session_id: str
    conversation_id: int
    prompt_id: int
    round_number: int
    user_input: str
    document_ids: int | list[int]
    knowledge_base_id: int
    story_id: Optional[str]
    data: dict

@service
class UserStoryChatAgentService:
    """用户故事agent服务层"""
    prompt_service:PromptService
    config_service:ConfigService
    conversation_service: ConversationService
    user_story_service: UserStoryService
    kmverse_util:KmverseUtil
    def __init__(self):
        pass

    def set_init(self):
        """初始化agent"""
        # 初始化模型
        model_config = self.config_service.data["ai_verse"]
        self.model = ChatDeepSeek(
            model=model_config["model_name"],
            api_base=model_config["api_base"],
            api_key=model_config["api_key"]
        )

        # 初始化数据库连接池
        db_config = self.config_service.data['database']
        db_config_str = f"postgresql://{db_config['db_account']}:{quote_plus(db_config['db_password'])}@{db_config['host']}:{db_config['port']}/{db_config['db_name']}"
        connection_kwargs = {
            "autocommit": True,
            "prepare_threshold": 0,
        }
        self.pool = ConnectionPool(
            conninfo=db_config_str,
            max_size=20,
            kwargs=connection_kwargs,
        )
        self.pool.open()  # 显式打开连接池

        # 初始化检查点
        self.checkpointer = PostgresSaver(self.pool)
        self.checkpointer.setup()

        # 初始化图
        self.graph = None
        self.build_graph()

    def build_graph(self):
        """构建图"""
        builder = StateGraph(State)
        # 添加节点
        builder.add_node("insert_human_chat", self.insert_human_chat)
        builder.add_node("query_knowledge", self.query_knowledge)
        builder.add_node("get_document", self.get_document)
        builder.add_node("set_system_prompt", self.set_system_prompt)
        builder.add_node("get_latest_user_stories", self.get_latest_user_stories)
        builder.add_node("set_user_message",self.set_user_message)
        builder.add_node("chat", self.chat)
        builder.add_node("get_new_user_story_str", self.get_new_user_story_str)
        builder.add_node("get_user_story_summary", self.get_user_story_summary)
        builder.add_node("get_new_user_story_json", self.get_new_user_story_json)
        builder.add_node("insert_user_story", self.insert_user_story)
        builder.add_node("insert_AI_chat", self.insert_AI_chat)
        builder.add_node("return_data", self.return_data)

        # 添加边
        builder.set_entry_point("insert_human_chat")
        builder.add_edge("insert_human_chat","query_knowledge")

        builder.add_conditional_edges("query_knowledge",self.judge,{
            "common chat":"get_document",
            "card chat":"set_system_prompt"
        })
        # builder.add_edge("query_knowledge","get_document")
        builder.add_edge("get_document","set_system_prompt")
        builder.add_edge("set_system_prompt","get_latest_user_stories")
        builder.add_edge("get_latest_user_stories","set_user_message")
        builder.add_edge("set_user_message","chat")
        builder.add_edge( "chat","get_new_user_story_str")
        builder.add_conditional_edges("get_new_user_story_str",self.judge,{
            "common chat": "get_user_story_summary",
            "card chat": "get_new_user_story_json"
        })
        builder.add_edge("get_user_story_summary","get_new_user_story_json")
        builder.add_conditional_edges("get_new_user_story_json",self.judge,{
            "common chat": "insert_user_story",
            "card chat": "insert_AI_chat"
        })
        builder.add_edge("insert_user_story","insert_AI_chat")
        builder.add_edge("insert_AI_chat","return_data")
        builder.set_finish_point("return_data")
        self.graph = builder.compile(checkpointer=self.checkpointer)

    def judge(self,state:State)->str:
        """根据story_id是否为None判断是正式对话还是小卡片对话,返回0代表正式对话，返回1代表小卡片对话"""
        if state["story_id"] is None:
            return "common chat"
        else:
            return "card chat"


    def query_knowledge(self, state: State) -> dict:
        """查询知识库"""
        if state["knowledge_base_id"] is not None:
            knowledges = self.kmverse_util.retrieval(state["user_input"], state["knowledge_base_id"])
            # 引用文档保存
            # 保存至状态
            data = state["data"]
            data["knowledge_results"] = ""
            for knowledge in knowledges:
                data["knowledge_results"] += knowledge["text"]+"\n"
        else:
            # 保存至状态
            data = state["data"]
            data["knowledge_results"] = ""
        HaivenLogger.get().logger.info(f"Session id:{state['session_id']},查询知识库成功（对话完成2/12）")
        return {"data": state["data"]}

    def set_no_think(self,ori_messages:str)->str:
        """设置不思考后缀"""
        return ori_messages+"/no_think"

    def insert_human_chat(self,state:State):
        """插入用户消息至数据库"""
        # 插入对话详情表（用户）
        self.conversation_service.add_chat_session_detail(
            session_id=state["session_id"],
            conversation_id=state["conversation_id"],
            user_flag="1",
            user_input=state["user_input"],
            prompt_id=state["prompt_id"],
            ref_document_id=str(state["document_ids"]),
            round_number=state["round_number"])
        HaivenLogger.get().logger.info(f"Session id:{state['session_id']},插入用户消息至数据库成功（对话完成1/12）")

    def get_document(self,state:State)->dict:
        """document绑定conversation id并且获取文档内容"""
        document_context = self.conversation_service.get_document_context_from_kmverse(document_ids=state["document_ids"],
                                                                                       user_query=state["user_input"])
        # 保存至状态
        data = state["data"]
        data["document_context"] = document_context
        HaivenLogger.get().logger.info(f"Session id:{state['session_id']},获取用户文档内容成功（对话完成3/12）")
        return {"data":data}

    def set_system_prompt(self,state:State)->dict:
        """设置系统提示词"""
        system_prompt = self.prompt_service.get_ai_prompt_by_id(state["prompt_id"])
        # 判断是否是第一轮对话，第一轮对话则直接加入系统提示词，第二轮则修改
        if state["round_number"]==1:
            messages = []
            messages.append({"role": "system", "content": system_prompt["content"]})
        else:
            messages = state["messages"]
            for message in messages:
                if message.type =="system":
                    message.content=system_prompt["content"]
        HaivenLogger.get().logger.info(f"Session id:{state['session_id']},设置系统提示词成功（对话完成4/12）")
        return {"messages":messages}

    def get_latest_user_stories(self,state:State)->dict:
        """获取最新用户故事"""
        # 根据conversation_id或者story_id获取历史最新用户故事
        if state["story_id"] is None:
            latest_user_stories = self.user_story_service.get_latest_user_story_by_conversation_id(conversation_id=state["conversation_id"])
        else:
            latest_user_stories = [self.user_story_service.get_user_story_by_story_id(story_id=state["story_id"])]
        # 将用户故事转换成json格式
        latest_user_stories_json = self.user_story_service.get_json_user_story(user_stories=latest_user_stories)
        # 保存至状态
        data = state["data"]
        data["latest_user_stories_json"] = latest_user_stories_json
        HaivenLogger.get().logger.info(f"Session id:{state['session_id']},获取最新用户故事成功（对话完成5/12）")
        return {"data": data}
    
    def set_user_message(self,state:State)->dict:
        # 设置用户消息
        user_message = f"用户需求:{state['user_input']}\n相关知识:{state['data']['knowledge_results']}\n用户文档{state['data'].get('document_context', '')}\n原始用户故事{state['data']['latest_user_stories_json']}"
        messages = []
        messages.append({"role": "user", "content": user_message})
        HaivenLogger.get().logger.info(f"Session id:{state['session_id']},设置用户消息成功（对话完成6/12）")
        return {"messages": messages}

    def chat(self, state: State) -> dict:
        """设置用户消息,发送消息，流式返回"""
        # 收集当前轮次的所有chunk
        full_response = []
        full_think = []
        # 获取回答
        writer = get_stream_writer()
        for chunk in self.model.stream(state["messages"]):
            if isinstance(chunk, (AIMessageChunk, AIMessage)):
                # 添加回复
                full_response.append(chunk.content)
                # 添加思考
                if "reasoning_content" in chunk.additional_kwargs:
                    think_message =chunk.additional_kwargs["reasoning_content"]
                    # 处理全是换行符的情况
                    if not bool(re.fullmatch(r'[\n]*', think_message)):
                        full_think.append(think_message)
                # 传递chunk供实时显示
                writer({"data": chunk,"data_type":"chat"})
        # 思考过程保存至状态
        data = state["data"]
        data["think_message"] = "".join(full_think)
        HaivenLogger.get().logger.info(f"Session id:{state['session_id']},获取AI回答成功（对话完成7/12）")
        # 确保最终合并为完整消息
        yield {"messages": [AIMessage(content="".join(full_response))],"data":data}

    def get_new_user_story_str(self,state:State)->dict:
        """截取ai回答中的user_story"""
        # 提取回答中的user_story数据
        user_story_str = self.conversation_service.get_special_data_no_think(llm_ans=state["messages"][-1].content)
        # 保存至状态
        data = state["data"]
        data["new_user_story_str"] = user_story_str
        HaivenLogger.get().logger.info(f"Session id:{state['session_id']},截取ai回答中的user_story成功（对话完成8/12）")
        return {"data": data}

    def get_user_story_summary(self,state:State)->dict:
        """获取这一批user_story的整体概述"""
        # 获取user_story整体概述
        user_story_prompt = self.prompt_service.get_user_story_summary_prompt(state["data"]["new_user_story_str"])
        user_story_summary_info = self.model.invoke(self.set_no_think(user_story_prompt))
        # 保存至状态
        data = state["data"]
        data["new_user_story_summary"] = user_story_summary_info.content
        HaivenLogger.get().logger.info(f"Session id:{state['session_id']},获取user_story整体概述成功（对话完成9/12）")
        return {"data": data}


    def get_new_user_story_json(self,state:State)->dict:
        """将字符串user_story格式化为json"""
        # 格式化user_story
        user_story_list = self.user_story_service.get_user_story_by_json(
            user_story_str=state["data"]["new_user_story_str"],
            user_story_summary=state["data"].get("new_user_story_summary",None))
        # 保存至状态
        data = state["data"]
        data["return_user_story"] = user_story_list
        HaivenLogger.get().logger.info(
            f"Session id:{state['session_id']},user_story格式化为json成功")
        return {"data": data}


    def insert_user_story(self,state:State)->dict:
        """插入生成的user_story至数据库"""
        # 格式化user_story
        user_story_list = self.user_story_service.get_user_story_by_json(user_story_str=state["data"]["new_user_story_str"],
                                                                         user_story_summary=state["data"]["new_user_story_summary"])
        # 保存user_story至数据库
        self.user_story_service.save_user_story_v2(conversation_id=state["conversation_id"],
                                                               round_number=state["round_number"],
                                                               user_story_list=user_story_list)
        # 根据conversation_id查询最新用户故事
        user_stories = self.user_story_service.get_latest_user_story_by_conversation_id(conversation_id=state["conversation_id"])
        # 保存至状态
        data = state["data"]
        data["return_user_story"] = user_stories
        HaivenLogger.get().logger.info(f"Session id:{state['session_id']},插入生成的user_story至数据库成功（对话完成10/12）")
        return {"data": data}

    def insert_AI_chat(self,state:State):
        """插入AI消息至数据库"""
        # 插入对话详情表（AI）
        self.conversation_service.add_chat_session_detail(
            session_id=state["session_id"],
            conversation_id=state["conversation_id"],
            user_flag="0",
            user_input=state["data"]["think_message"],
            prompt_id=state["prompt_id"],
            ref_document_id=str(state["document_ids"]),
            reg_document_id="None",
            round_number=state["round_number"])
        HaivenLogger.get().logger.info(f"Session id:{state['session_id']},插入AI消息至数据库成功（对话完成11/12）")

    def return_data(self,state:State)->dict:
        """返回前端所需数据"""
        writer = get_stream_writer()
        writer({"data_type": "return","data":{"user_stories":state["data"]["return_user_story"],"think_message":state["data"]["think_message"]}})

    def graph_stream(self,session_id: str,
                        conversation_id: int,
                        prompt_id: int,
                        round_number: int,
                        user_input: str,
                        knowledge_base_id:int,
                        document_ids: list[int]=None,
                        story_id:int=None)->str:
        """调用图,并且返回格式化数据"""
        # 会话隔离
        config = {"configurable": {"thread_id": session_id}}

        # 标记是否处于think
        think_flag = True
        for chunk in self.graph.stream({"messages": [],
                                                         "session_id": session_id,
                                                         "conversation_id": conversation_id,
                                                         "prompt_id":prompt_id,
                                                         "round_number": round_number,
                                                         "user_input":user_input,
                                                         "document_ids": document_ids,
                                                         "knowledge_base_id": knowledge_base_id,
                                                         "story_id":story_id,
                                                         "data":{}
                                                         },
                                                        stream_mode="custom",
                                                        config=config):
            message_type = chunk["data_type"]
            data = chunk["data"]
            if message_type=="chat":
                # 按照是否携带思考信息进行处理
                if "reasoning_content" in data.additional_kwargs:
                    message = data.additional_kwargs["reasoning_content"]
                    # 处理全是换行符的情况
                    if not bool(re.fullmatch(r'[\n]*', message)):
                        yield json.dumps({"think": message}) + "\n\n"
            elif message_type=="return":
                # 获取前端需要的数据
                if story_id is None:
                    return_data = self.conversation_service.get_user_story_api_return_data(data["user_stories"], data["think_message"])
                else:
                    return_data = self.conversation_service.get_update_user_story_api_return_data(data["user_stories"], data["think_message"])
                data = json.dumps(ApiResponse.success(data=return_data, message="success",
                                                      conversation_id=conversation_id, session_id=session_id),
                                  ensure_ascii=False)
                HaivenLogger.get().logger.info(
                    f"Session id:{session_id},获取前端需要的数据成功（对话完成12/12）")
                yield json.dumps({"body": data}) + "\n\n"



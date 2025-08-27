'''
状态：一个共享数据结构，表示应用程序的当前快照。它可以是任何 Python 类型，但通常是 TypedDict 或 Pydantic BaseModel。
节点：Python 函数，用于编码代理的逻辑。它们以当前 状态 作为输入，执行一些计算或副作用，并返回更新后的 状态。
边：Python 函数，根据当前 状态 确定要执行的下一个 节点。它们可以是条件分支或固定转换。
节点 和 边 仅仅是 Python 函数 - 它们可以包含 LLM 或普通的 Python 代码。
节点完成工作，边指示下一步要做什么.
'''
# pip install -qU "langchain[anthropic]" to call the model
#
# from langgraph.prebuilt import create_react_agent
#
# def get_weather(city: str) -> str:
#     """获取 指定天气信息 """
#     return f"It's always sunny in {city}!"
#
# agent = create_react_agent(
#     model="anthropic:claude-3-7-sonnet-latest", #LLM
#     tools=[get_weather], # tool
#     prompt="You are a helpful assistant"
# )
#
# # Run the agent
# agent.invoke(
#     {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
# )
from langchain_community.document_loaders import WebBaseLoader
# WebBaseLoader获取博客内容用于RAG
urls = [
    "https://blog.csdn.net/xnuscd/article/details/143474722"
]

docs = [WebBaseLoader(url).load() for url in urls]

## 文档切块
from langchain_text_splitters import RecursiveCharacterTextSplitter
docs_list = [item for sublist in docs for item in sublist]

text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=100, chunk_overlap=50
)
doc_splits = text_splitter.split_documents(docs_list)

#创建检索
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings

vectorstore = InMemoryVectorStore.from_documents( # 内存向量存储
    documents=doc_splits, embedding=OpenAIEmbeddings()
)
retriever = vectorstore.as_retriever() #检索器
from langchain.tools.retriever import create_retriever_tool

retriever_tool = create_retriever_tool( # 检索Tool
    retriever,
    "retrieve_blog_posts",
    "Search and return information about Lilian Weng blog posts.",
)

#### 构建RAG图的 nodes、edges
from langgraph.graph import MessagesState
from langchain.chat_models import init_chat_model
#
response_model = init_chat_model("openai:gpt-4.1", temperature=0)
'''
组件将在MessagesState —— 图上运行，该State包含一个messages 键，其中包含一条消息
'''
def generate_query_or_respond(state: MessagesState):
    response = ( # 传入 状态state的messages
        response_model
        .bind_tools([retriever_tool]).invoke(state["messages"])
    )
    return {"messages": [response]}
# input = {
#     "messages": [
#         {
#             "role": "user",
#             "content": "What does Lilian Weng say about types of reward hacking?",
#         }
#     ]
# }
# generate_query_or_respond(input)["messages"][-1].pretty_print()
#
# ================================== Ai Message ==================================
# Tool Calls:
# retrieve_blog_posts (call_tYQxgfIlnQUDMdtAhdbXNwIM)
# Call ID: call_tYQxgfIlnQUDMdtAhdbXNwIM
# Args:
#     query: types of reward hacking

## 添加一个条件边 — grade_documents — 来判断检索到的文档是否与问题相关
##GradeDocuments 评分Pydantic、
# 决策：generate_answer——前进 或 rewrite_question——重写
from pydantic import BaseModel, Field
from typing import Literal

Grade_Prompt= (
    "You are a grader assessing relevance of a retrieved document to a user question. \n "
    "Here is the retrieved document: \n\n {context} \n\n"
    "Here is the user question: {question} \n"
    "If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n"
    "Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."
)

class GradeDocuments(BaseModel):
    """ 相关性评分 yes / no"""
    binary_score: str = Field(
        description="Relevance score: 'yes' if relevant, or 'no' if not relevant"
    )

grader_model = init_chat_model("openai:gpt-4.1", temperature=0)

def grade_documents(
    state: MessagesState,
) -> Literal["generate_answer", "rewrite_question"]:

    question = state["messages"][0].content
    context = state["messages"][-1].content

    prompt = Grade_Prompt.format(question=question, context=context)
    response = (
        grader_model # Pydantic 结构化输出
        .with_structured_output(GradeDocuments).invoke(
            [{"role": "user", "content": prompt}]
        )
    )
    score = response.binary_score

    if score == "yes": ## 根据GradeDocuments结果，输出决策
        return "generate_answer"
    else:
        return "rewrite_question"

from langchain_core.messages import convert_to_messages
# convert_to_messages 转为 BaseMessage，
# 也可以直接用
# from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
input = {
    "messages": convert_to_messages(
        [
            {
                "role": "user",
                "content": "What does Lilian Weng say about types of reward hacking?",
            },
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "1",
                        "name": "retrieve_blog_posts",
                        "args": {"query": "types of reward hacking"},
                    }
                ],
            },
            {"role": "tool", "content": "meow", "tool_call_id": "1"},
        ]
    )
}
grade_documents(input)

REWRITE_PROMPT = (
    "Look at the input and try to reason about the underlying semantic intent / meaning.\n"
    "Here is the initial question:"
    "\n ------- \n"
    "{question}"
    "\n ------- \n"
    "Formulate an improved question:"
)

# 构建 rewrite_question 节点，
# 如果没找到相关的文档 即 GradeDocuments 为No
# ，则重新理解用户问题
def rewrite_question(state: MessagesState):
    """Rewrite the original user question."""
    messages = state["messages"]
    question = messages[0].content
    prompt = REWRITE_PROMPT.format(question=question)
    response = response_model.invoke([{"role": "user", "content": prompt}])
    return {"messages": [{"role": "user", "content": response.content}]}

GENERATE_PROMPT = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer the question. "
    "If you don't know the answer, just say that you don't know. "
    "Use three sentences maximum and keep the answer concise.\n"
    "Question: {question} \n"
    "Context: {context}"
)
# 构建 generate_answer 节点；通过GradeDocuments=Yes，根据问题、检索进行生成
def generate_answer(state: MessagesState):
    """Generate an answer."""
    question = state["messages"][0].content
    context = state["messages"][-1].content
    prompt = GENERATE_PROMPT.format(question=question, context=context)
    response = response_model.invoke([{"role": "user", "content": prompt}])
    return {"messages": [response]}

## 组装 Graph

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition

# MessagesState：这是一个自定义的状态结构（通常是TypedDict或pydantic.BaseModel）
workflow = StateGraph(MessagesState) #创建工作流，基于MessagesState的状态图实例

# 添加 Node
workflow.add_node(generate_query_or_respond)
# 添加一个名为"retrieve"的节点，类型为ToolNode（工具节点），绑定了retriever_tool
workflow.add_node("retrieve", ToolNode([retriever_tool]))
workflow.add_node(rewrite_question)
workflow.add_node(generate_answer)
# 添加 edge
workflow.add_edge(START, "generate_query_or_respond")

# 决定是否要检索
workflow.add_conditional_edges(
    "generate_query_or_respond",
    tools_condition, # 条件函数：用该函数判断下一步
    {
        # 条件映射：函数返回值 → 目标节点
        "tools": "retrieve", # 若条件函数返回"tools"，则下一步执行"retrieve"节点
        END: END,# 若条件函数返回END，则直接结束工作流
    },
)

# 调用"retrieve"节点后 的edge
workflow.add_conditional_edges(
    "retrieve", # 起点节点：从检索节点出发
    grade_documents,# 条件函数：评估检索到的文档是否有效
)
workflow.add_edge("generate_answer", END) # 结束edge
workflow.add_edge("rewrite_question", "generate_query_or_respond")

# 编译
graph = workflow.compile()

# 可视化Graph
from IPython.display import Image, display

display(Image(graph.get_graph().draw_mermaid_png()))

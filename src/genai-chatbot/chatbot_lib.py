"""GenAI 聊天机器人核心库。

LLM 通过 LangChain 的
OpenAI 兼容封装（ChatOpenAI）指向 MaaS 统一推理入口，会话历史仍存 DCS（Redis）。
"""

import os

from langchain.memory import RedisChatMessageHistory
from langchain_openai import ChatOpenAI

# MaaS OpenAI 兼容端点（与 src/llm/maas_client.py 一致）
MAAS_CHAT_BASE_URL = os.environ.get(
    "MAAS_CHAT_BASE_URL", "https://api.modelarts-maas.com/v2"
)
MAAS_API_KEY = os.environ.get("HUAWEICLOUD_API_KEY", "")
DEFAULT_MODEL = os.environ.get("MODEL_NAME", "deepseek-v3.2")

redis_url = os.environ.get("REDIS_URL")


def get_llm():
    """返回指向 MaaS 的 LLM（OpenAI 兼容）。"""
    return ChatOpenAI(
        model=DEFAULT_MODEL,
        api_key=MAAS_API_KEY,
        base_url=MAAS_CHAT_BASE_URL,
        temperature=0,
        max_tokens=8000,
    )


def get_chat_history():
    return RedisChatMessageHistory(
        session_id="username", url=redis_url, key_prefix="chat_history:"
    )


def get_memory(session_id, url, key_prefix):
    """创建带摘要的会话记忆（摘要依赖 LLM，已替换为 MaaS）。"""
    llm = get_llm()
    chat_history = RedisChatMessageHistory(
        session_id=session_id, url=url, key_prefix=key_prefix
    )
    from langchain.memory import ConversationSummaryBufferMemory

    memory = ConversationSummaryBufferMemory(
        ai_prefix="AI Assistant",
        llm=llm,
        max_token_limit=1024,
        chat_memory=chat_history,
    )
    return memory


def get_chat_response(input_text, memory):
    """对话入口：用 LangChain ConversationChain 生成回复。"""
    llm = get_llm()
    template = """The following is a friendly conversation between a human and an AI.
AI provide very concise responses. If the AI does not know the answer to a question, it truthfully says it does not know.
Current conversation:{history}. Human: {input}  AI Assistant:"""
    from langchain.chains import ConversationChain
    from langchain.prompts.prompt import PromptTemplate

    prompt = PromptTemplate(input_variables=["history", "input"], template=template)
    conversation = ConversationChain(llm=llm, memory=memory, prompt=prompt, verbose=False)
    return conversation.predict(input=input_text)
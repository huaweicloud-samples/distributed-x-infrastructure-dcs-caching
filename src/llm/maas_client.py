"""华为云 ModelArts Studio（MaaS）推理客户端。

封装 MaaS 预置模型服务的 OpenAI 兼容调用入口。模型推理统一
收敛到这里（chat / stream_chat / embed），业务代码不再直连模型端点。

使用方式：
    from llm.maas_client import MaaSClient
    client = MaaSClient()
    resp = client.chat(messages=[{"role": "user", "content": "你好"}])

依赖：pip install openai
"""

import os

from openai import OpenAI

# MaaS 预置模型部署名（业务代码直接选用）
DEFAULT_CHAT_MODEL = "deepseek-v3.2"
DEFAULT_EMBED_MODEL = "bge-m3"


class MaaSClient:
    """ModelArts Studio 预置模型推理客户端。

    端点：
      - 对话：https://api.modelarts-maas.com/v2
      - 嵌入：https://api.modelarts-maas.com/v1

    通过环境变量配置：
      - HUAWEICLOUD_API_KEY : 在华为云「我的凭证」页面获取
      - MAAS_CHAT_BASE_URL  : 自定义对话端点（可选）
      - MAAS_EMBED_BASE_URL : 自定义嵌入端点（可选）
    """

    def __init__(
        self,
        api_key: str | None = None,
        chat_base_url: str | None = None,
        embed_base_url: str | None = None,
    ):
        self.api_key = api_key or os.environ.get("HUAWEICLOUD_API_KEY", "")
        chat_url = (
            chat_base_url
            or os.environ.get("MAAS_CHAT_BASE_URL")
            or "https://api.modelarts-maas.com/v2"
        )
        embed_url = (
            embed_base_url
            or os.environ.get("MAAS_EMBED_BASE_URL")
            or "https://api.modelarts-maas.com/v1"
        )
        self._chat = OpenAI(base_url=chat_url, api_key=self.api_key)
        self._embed = OpenAI(base_url=embed_url, api_key=self.api_key)

    def chat(self, messages: list[dict], model: str = DEFAULT_CHAT_MODEL, **kwargs):
        """同步对话推理。"""
        return self._chat.chat.completions.create(model=model, messages=messages, **kwargs)

    def stream_chat(self, messages: list[dict], model: str = DEFAULT_CHAT_MODEL, **kwargs):
        """流式对话推理，返回 OpenAI Stream 对象。"""
        return self._chat.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            stream_options={"include_usage": True},
            **kwargs,
        )

    def embed(self, text: str | list[str], model: str = DEFAULT_EMBED_MODEL) -> list[list[float]]:
        """文本嵌入向量生成。"""
        response = self._embed.embeddings.create(model=model, input=text)
        return [item.embedding for item in response.data]
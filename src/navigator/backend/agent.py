"""缓存集群指标分析与优化建议（LLM 封装）。

模型能力统一走 MaaSClient（OpenAI 兼容，默认 DeepSeek），
入口函数签名保持不变，供 FastAPI 后端调用。
"""

import json
import logging
import os

from llm.maas_client import MaaSClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.environ.get("MODEL_NAME", "deepseek-v3.2")

INSTRUCTIONS = """
Analyze the following cache cluster metrics and provide specific optimization recommendations.

Input Parameters:
1. Cluster Type: [Valkey/Redis/Memcached]
2. Current Node Type: [e.g., cache node type]
3. Number of Nodes: [X]
4. Eviction Policy: [if applicable]

Key Metrics (provide values for the last 7 days):
1. Memory Usage (freeable memory, usage %, swap)
2. CPU Metrics (utilization %, engine CPU %)
3. Network (bytes in/out, packets in/out)
4. Cache Performance (misses, hits, evictions, connections)
5. Latency (get/set)

Based on these metrics, provide:
1. Analysis of current performance bottlenecks
2. Specific recommendations (sizing, scaling strategy, memory management, eviction policy, connection pooling)
3. Cost-effectiveness analysis of proposed changes
4. Priority order for implementation
5. Expected performance improvements

Include relevant best practices and consider both performance and cost implications.
"""

NAMING_SYSTEM_PROMPT = """
Welcome to Cache Navigator
Monitor and manage your cache cluster with real-time insights and performance metrics.
"""


def _client():
    return MaaSClient()


def invoke_llm(cluster_info: str) -> str:
    """用 MaaS 生成优化建议。"""
    client = _client()
    messages = [
        {"role": "system", "content": INSTRUCTIONS},
        {"role": "user", "content": "The data for the cluster is: " + cluster_info},
    ]
    resp = client.chat(messages=messages, model=DEFAULT_MODEL)
    return resp.choices[0].message.content


def perform_recommendation(prompt):
    """供 FastAPI /api/cache/recommend 调用的入口。"""
    answer = invoke_llm(prompt)
    return {"statusCode": 200, "body": json.dumps(answer)}


def function_handler(event, context):
    """navigator 调用入口。"""
    body = event.get("body", "") if isinstance(event, dict) else str(event)
    answer = invoke_llm(body)
    return {"statusCode": 200, "body": json.dumps(answer)}


if __name__ == "__main__":
    print(function_handler({"body": "CPU 89%"}, None))
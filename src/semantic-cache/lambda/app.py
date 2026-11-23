"""语义缓存（Semantic Cache）函数入口。

流程：查询向量化 → DCS（Redis）KNN 命中缓存直接返回；未命中则走 MaaS
（OpenAI 兼容）生成答案并回写缓存。知识库增强与生成统一由 MaaS 提供，
部署说明见 docs/deployment-guide.md。
"""

import hashlib
import json
import os
import time

import numpy as np
import redis
from llm.maas_client import MaaSClient

EMBED_MODEL = os.environ.get("EMBEDDING_MODEL", "bge-m3")
CHAT_MODEL = os.environ.get("MODEL_NAME", "deepseek-v3.2")


def _embed(query):
    return MaaSClient().embed([query], model=EMBED_MODEL)[0]


def _generate(enhanced_query):
    client = MaaSClient()
    resp = client.chat(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. Use available context to answer; "
                    "if information is insufficient, say so based on available data."
                ),
            },
            {"role": "user", "content": enhanced_query},
        ],
        model=CHAT_MODEL,
    )
    return resp.choices[0].message.content


def lambda_handler(event, context=None):
    """完整语义缓存逻辑：先查缓存 → 未命中走 MaaS 生成 → 回写缓存。"""
    try:
        if "body" in event:
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
        else:
            body = event

        query = body.get("query", "").strip()
        score_threshold = body.get("score_threshold", 0.7)

        if not query:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "No query provided"}),
            }

        valkey_client = redis.Redis(
            host=os.environ["VALKEY_HOST"],
            port=int(os.environ.get("VALKEY_PORT", "6379")),
            decode_responses=False,
        )

        query_vector = np.array(_embed(query), dtype=np.float32)

        # 1. 先查 DCS 缓存
        cache_start = time.time()
        search_cmd = [
            "FT.SEARCH",
            "idx:pqa_vss",
            "*=>[KNN 1 @question_vector $query_vec AS score]",
            "PARAMS",
            "2",
            "query_vec",
            query_vector.tobytes(),
        ]
        cache_result = valkey_client.execute_command(*search_cmd)
        cache_duration = (time.time() - cache_start) * 1000

        if cache_result and len(cache_result) > 2:
            fields = cache_result[2]
            score = 0.0
            if isinstance(fields, list):
                for i in range(0, len(fields), 2):
                    if i + 1 < len(fields) and fields[i] == b"score":
                        score = float(fields[i + 1])
                        break
            if score <= score_threshold:
                doc_id = cache_result[1]
                doc_id_str = doc_id.decode("utf-8") if isinstance(doc_id, bytes) else doc_id
                hash_data = valkey_client.hgetall(doc_id_str)
                cached_question = hash_data.get(b"question", b"").decode("utf-8")
                cached_answer = hash_data.get(b"answer", b"").decode("utf-8")
                return {
                    "statusCode": 200,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps(
                        {
                            "answer": cached_answer,
                            "question": cached_question,
                            "source": "valkey_cache",
                            "response_time_ms": cache_duration,
                            "score": score,
                        }
                    ),
                }

        # 2. 缓存未命中（或分数过低）→ MaaS 生成
        kb_start = time.time()
        enhanced_query = (
            f"{query}\n\nInstructions: Use available context clues and user comments to "
            "make reasonable inferences. Provide the best possible answer based on available "
            "data. Frame responses positively."
        )
        answer = _generate(enhanced_query)
        kb_duration = (time.time() - kb_start) * 1000

        # 3. 回写缓存
        cache_key = f"pqa:{int(hashlib.sha256(query.encode()).hexdigest(), 16) % 1000000}"
        valkey_client.hset(
            cache_key,
            mapping={
                "question": query,
                "answer": answer,
                "question_vector": query_vector.tobytes(),
            },
        )

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "answer": answer,
                    "question": query,
                    "source": "knowledge_base",
                    "response_time_ms": kb_duration,
                    "cache_time_ms": cache_duration,
                    "score": 1.0,
                }
            ),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)}),
        }
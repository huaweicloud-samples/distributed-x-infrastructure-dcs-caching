"""向量检索示例：文档分块 → 向量化 → 存 DCS（Redis）→ KNN 检索。

向量化改为
MaaS 嵌入端点（OpenAI 兼容，默认 bge-m3，1024 维），向量结构与原例一致。
"""

import os

import numpy as np
import valkey
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from openai import OpenAI
from valkey.commands.search.field import VectorField
from valkey.commands.search.query import Query

# 缓存连接（DCS Redis，valkey 客户端走 RESP 协议）
VALKEY_ENDPOINT = os.environ.get("REDIS_HOST", "")
VALKEY_CLUSTER_MODE = os.environ.get("REDIS_CLUSTER_MODE", "false").lower() == "true"
VALKEY_PORT = int(os.environ.get("REDIS_PORT", "6379"))

# 待向量化的网页（可配置；默认使用公开文档页）
WEBSITE_URL = os.environ.get(
    "WEBSITE_URL",
    "https://www.huaweicloud.com/product/dcs.html",
)
QUERY_STR = "Which engines does the cache service support?"

# MaaS 嵌入端点（OpenAI 兼容）
EMBED_BASE_URL = os.environ.get("MAAS_EMBED_BASE_URL", "https://api.modelarts-maas.com/v1")
EMBED_MODEL = os.environ.get("EMBEDDING_MODEL", "bge-m3")
_embed_client = OpenAI(
    base_url=EMBED_BASE_URL,
    api_key=os.environ.get("HUAWEICLOUD_API_KEY", ""),
)

VECTOR_DIMENSIONS = 1024
INDEX_NAME = "vectorIndex"


def embed_documents(texts):
    resp = _embed_client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [item.embedding for item in resp.data]


def embed_query(text):
    return embed_documents([text])[0]


# Step 1. 加载网页并分片
loader = WebBaseLoader(web_path=WEBSITE_URL)
pages = loader.load()
text_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", ".", " "],
    chunk_size=1000,
    chunk_overlap=200,
)
chunks = text_splitter.split_documents(pages)
print(f"Loaded and split content into {len(chunks)} chunks")

# Step 2. 创建向量索引
if VALKEY_CLUSTER_MODE:
    client = valkey.ValkeyCluster(host=VALKEY_ENDPOINT, port=VALKEY_PORT, decode_responses=True)
else:
    client = valkey.Valkey(host=VALKEY_ENDPOINT, port=VALKEY_PORT, decode_responses=True)

try:
    client.ft(index_name=INDEX_NAME).info()
    print(f'Index "{INDEX_NAME}" already exists')
except valkey.ResponseError as e:
    if "not found" not in str(e):
        raise e
    print(f'Creating index "{INDEX_NAME}"')
    client.ft(index_name=INDEX_NAME).create_index(
        [
            VectorField(
                "embed",
                "HNSW",
                {
                    "TYPE": "FLOAT32",
                    "DIM": VECTOR_DIMENSIONS,
                    "DISTANCE_METRIC": "COSINE",
                },
            )
        ]
    )


def to_bytes(x):
    return np.array(x, dtype=np.float32).tobytes()


# Step 3. 分片向量化并写入
for i, chunk in enumerate(chunks):
    content = chunk.page_content
    vector_embedding = to_bytes(embed_documents([content]))
    client.hset(f"chunkId:{i}", mapping={"embed": vector_embedding, "text": content})

# Step 4. KNN 检索
query = Query("*=>[KNN 3 @embed $vec as score]").return_fields("id", "score").dialect(2)
query_params = {"vec": to_bytes(embed_query(QUERY_STR))}
results = client.ft(index_name=INDEX_NAME).search(query, query_params).docs

print(f"\nGot {len(results)} results:")
for idx, item in enumerate(results):
    print(f">>> Result #{idx}: {item}")

if len(results) > 0:
    print(f'\nShowing the raw chunk for "{results[0].id}":')
    print(client.hget(results[0].id, "text"))
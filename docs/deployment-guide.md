# 部署指导

本文档说明 `distributed-x-infrastructure-dcs-caching` 各样例的部署方式。共享底座（VPC + DCS + RDS + OBS）一次拉起，各样例按需运行。

## 一、共享底座部署

```bash
cd infra
export HW_ACCESS_KEY="<ak>"
export HW_SECRET_KEY="<sk>"
export TF_VAR_redis_password="<redis-password>"
export TF_VAR_rds_password="<mysql-password>"
terraform init
terraform plan
terraform apply -auto-approve
terraform output
```

关键输出：`redis_endpoint`、`memcached_endpoint`、`mysql_endpoint`、`obs_bucket_name`、`vpc_id`、`subnet_id`。

## 二、样例运行

> 连接信息一律通过环境变量传入（华为云「我的凭证」页面获取 Access Key；DCS/RDS 密码在部署时设置）。

### 1. 数据库查询缓存（`src/database-caching`）

```bash
pip install -r requirements.txt
mysql -h "<mysql_endpoint>" -uroot -p"<mysql-password>" < seed.sql
REDIS_URL="redis://:<redis-password>@<dcs-endpoint>:6379/0" \
DB_HOST="<mysql_endpoint>" DB_USER=root DB_PASS="<mysql-password>" DB_NAME=tutorial \
python example.py
```

### 2. 会话存储（`src/session-store`）

```bash
pip install -r requirements.txt
export REDIS_URL="redis://:<redis-password>@<dcs-endpoint>:6379/0"
python example-2.py   # 浏览器访问 http://localhost:5000/
```

### 3. LLM 对话 + 会话缓存（`src/genai-chatbot`）

```bash
export HUAWEICLOUD_API_KEY="<maas-api-key>"
export REDIS_URL="redis://:<redis-password>@<dcs-endpoint>:6379/0"
pip install -r requirements.txt
streamlit run chatbot_app.py
```

### 4. 特征存储（`src/lambda-feature-store`）

- `get_movie_recommendations.py` / `put_movie_recommendations.py`：FunctionGraph 函数，handler 签名 `handler(event, context)`。
- `put` 函数从 OBS 读取 `batchpredictions.json` 写入 DCS；`get` 函数按 `userId` + `rank` 读取。
- 需在 FunctionGraph 控制台创建两个函数，配置环境变量 `REDIS_URL`（get）/ `REDIS_URL` + `OBS_BUCKET` + `REGION`（put），并将函数 VPC 打到共享 VPC。

### 5. 向量检索（`src/vector-search`）

```bash
export HUAWEICLOUD_API_KEY="<maas-api-key>"
export REDIS_HOST="<dcs-endpoint>"
export WEBSITE_URL="https://www.huaweicloud.com/product/dcs.html"
pip install -r requirements.txt
python main.py
```

### 6. 语义缓存（`src/semantic-cache`）

- `lambda/app.py`：先查 DCS 向量缓存，未命中走 MaaS 生成并回写。
- 环境变量：`VALKEY_HOST`、`HUAWEICLOUD_API_KEY`、`EMBEDDING_MODEL`、`MODEL_NAME`。

### 7. Feast 特征存储（`src/feast`）

- `feature_repo/feature_store.yaml`：在线存储 `redis`（指向 DCS），离线存储 `file`（本地 Parquet）。
- `feature_repo/features.py`：离线源用 `FileSource`（Parquet）。
- 依赖 `feast`（本地/redis provider），运行 `feast apply` 后经 `run.py` 训练与在线推理。

### 8. DynamoDB 兼容协议集成缓存（`src/dynamodb-cache-integration`）

- 纯客户端库，`CacheClient` 包一层「DCS + GeminiDB（DynamoDB 兼容）」读穿缓存。
- 需将 `dynamodb_client` 指向 GeminiDB 的 DynamoDB 兼容 endpoint，`redis_client` 指向 DCS。

### 9. 缓存管理工具 navigator / Agent 记忆 demo（`src/navigator` / `src/agentic-memory-with-valkey`）

- 后端连接信息经环境变量传入；模型推理统一走 `src/llm/maas_client.py`（MaaS）。
- 部署形态为容器（CCE）或本地 `docker-compose`，参见各目录 `README`（`docker-compose.yml`）。

### 10. 数据同步 / 代理 / DevOps 工具

- `src/blue-green-migration`（Redis 数据同步脚本）、`src/envoy-proxy-example`（双写代理配置）、`src/riot-example`（数据复制）均以脚本/配置形式给出，连接信息替换为 DCS 地址即可。
- 部署样例的 IaC（缓存实例）统一由 `infra/` 的 Terraform 提供。

## 三、可选服务说明

- **GeminiDB（DynamoDB 兼容）**：仅 `dynamodb-cache-integration` 样例需要，可在控制台单独创建，或在 `infra/` 中追加 `huaweicloud_geminidb_instance` 资源。
- **CCE**：`navigator` / `agentic-memory` 等容器化样例如需云上运行，可创建 CCE 集群部署镜像。
- **FunctionGraph**：`lambda-feature-store` / `semantic-cache` 的函数需在控制台上传代码包并绑定 VPC。
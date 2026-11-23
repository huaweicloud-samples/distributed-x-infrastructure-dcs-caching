# 架构说明

本实践围绕华为云 **DCS（分布式缓存服务）** 的常见缓存模式展开，共享一套 VPC 网络底座，按场景组合 DCS、RDS、OBS、FunctionGraph、MaaS 等华为云服务。

## 整体架构

```
┌────────────┐   Redis 协议   ┌──────────────────┐
│  客户端应用  │ ─────────────▶ │  DCS（Redis/     │
│ Web/CLI/LLM │                │  Memcached）      │
└────────────┘                └────────┬─────────┘
                                        │ 未命中
                        ┌───────────────┼───────────────┐
                        ▼               ▼               ▼
                 ┌────────────┐  ┌─────────────┐  ┌──────────┐
                 │ RDS(MySQL) │  │ MaaS(LLM/向 │  │ OBS(文件) │
                 │ 回源数据库  │  │ 量化)        │  │ 特征/对象 │
                 └────────────┘  └─────────────┘  └──────────┘
```

## 分层说明

### 网络底座

所有样例共享一个 VPC 及子网，安全组对内网放行缓存（Redis 6379 / Memcached 11211）、数据库（MySQL 3306）与应用（8080）端口。缓存与数据库实例部署在同一 VPC 内，避免公网暴露。

### 缓存层（DCS）

- **Redis 引擎**：承载数据库查询缓存、会话存储、特征存储、向量检索、语义缓存、LLM 会话等 Redis 协议场景。
- **Memcached 引擎**：承载 Memcached 兼容场景。
- 客户端通过 Redis 协议直连，DCS 提供内网域名与端口，密码鉴权可在实例创建时设置（建议启用）。

### 计算与回源层

- **RDS（MySQL）**：数据库查询缓存 / JDBC 缓存演示的回源数据库。
- **MaaS**：LLM 对话、语义缓存与向量化的统一推理入口（OpenAI 兼容，默认 DeepSeek / bge-m3）。
- **FunctionGraph + OBS**：特征存储、语义缓存等 Serverless 场景的计算与对象存储。

## 缓存模式一览

| 模式 | 样例目录 | 说明 |
|---|---|---|
| 缓存旁路（cache-aside） | `src/database-caching` | 查询先查缓存，未命中回源再回填 |
| 会话存储 | `src/session-store` / `src/flask-redis-session` | Web 会话状态持久化到 DCS |
| 特征存储 | `src/lambda-feature-store` / `src/feast` | ML 特征 / 预测结果缓存到 DCS |
| 向量检索 | `src/vector-search` | 向量化后 KNN 检索 |
| 语义缓存 | `src/semantic-cache` | 相似问答向量缓存，未命中走 MaaS |
| LLM 会话 / 记忆 | `src/genai-chatbot` / `src/agentic-memory-with-valkey` | 对话历史、Agent 记忆存 DCS |
| 数据同步 / 代理 | `src/blue-green-migration` / `src/envoy-proxy-example` / `src/riot-example` | 蓝绿切换、双写代理、数据复制 |
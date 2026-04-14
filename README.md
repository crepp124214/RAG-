# RAG 智能文档检索助手

基于 LLM 的企业级智能文档检索与知识问答平台，支持多模态文档解析、知识图谱构建和智能对话。

## 核心功能

| 功能 | 技术实现 |
|------|----------|
| **文档上传与处理** | 异步任务队列（RQ + Redis），支持 PDF/DOCX/TXT，分块策略优化 |
| **RAG 问答** | FastAPI + SSE 流式输出，DashScope Embedding 向量化，BGE Reranker 重排 |
| **多模态解析** | PyMuPDF 视觉提取，Qwen-VL 图像描述，文本+视觉混合检索 |
| **知识图谱** | Neo4j 图数据库，实体关系抽取，GraphRAG 检索降级策略 |
| **Tool Calling** | web_search / document_lookup 工具集成，流式 Tool Call 输出 |
| **多知识库** | 知识库隔离，文档/会话按知识库分离，支持独立管理 |
| **会话管理** | 多轮对话，Markdown 导出，会话置顶与搜索 |

## 技术栈

**前端：** Vue 3 + TypeScript + Vite + Element Plus + Pinia

**后端：** FastAPI + Pydantic + SQLAlchemy + Alembic + Uvicorn

**数据：** PostgreSQL + pgvector（向量检索），Neo4j（图数据库），Redis（任务队列）

**模型：** Qwen（通义千问）+ DashScope Embedding + BGE Reranker + Qwen-VL

## 快速开始

### 环境要求

- Python 3.10+ / Node.js 18+
- Docker Desktop

### 启动步骤

```bash
# 1. 配置环境变量
copy .env.example .env
# 编辑 .env 填入 DASHSCOPE_API_KEY

# 2. 启动依赖
docker run -d --name rag-postgres-pgvector -p 5433:5432 -e POSTGRES_PASSWORD=postgres ankane/pgvector:latest
docker run -d --name rag-redis -p 6379:6379 redis:7-alpine

# 3. 数据库迁移
python -m alembic upgrade head

# 4. 启动服务
start.bat dev
```

访问 http://127.0.0.1:5173

### 服务地址

| 服务 | 地址 |
|------|------|
| 前端 | http://127.0.0.1:5173 |
| 后端 API | http://127.0.0.1:8000/docs |

## 项目架构

```
├── frontend/          # Vue 3 SPA (Element Plus)
├── backend/          # FastAPI REST API
│   ├── api/         # 路由与 Schema
│   ├── app/         # 业务逻辑 (Services/Repositories)
│   └── infrastructure/  # 外部集成 (LLM/Vector/Queue)
├── worker/          # RQ 异步任务处理器
└── data/            # 文件存储
```

## 环境变量

| 配置项 | 说明 |
|--------|------|
| `DASHSCOPE_API_KEY` | 阿里云 API Key（必填） |
| `DATABASE_URL` | PostgreSQL 连接 |
| `REDIS_URL` | Redis 连接 |
| `NEO4J_URI` | Neo4j 连接（可选，GraphRAG） |

完整配置参考 `.env.example`。

## 许可证

MIT

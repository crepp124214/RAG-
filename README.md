# 多模态RAG检索问答平台

基于 LLM 的智能文档检索与知识问答平台，支持多模态文档解析、知识图谱构建和智能问答。

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Docker Desktop

### 启动步骤

```bash
# 1. 克隆仓库
git clone https://github.com/crepp124214/RAG-.git
cd RAG智能文档检索助手

# 2. 配置环境变量
copy .env.example .env
# 编辑 .env 填入必要配置（DASHSCOPE_API_KEY 等）

# 3. 启动依赖容器
docker run -d --name rag-postgres-pgvector -p 5433:5432 -e POSTGRES_PASSWORD=postgres ankane/pgvector:latest
docker run -d --name rag-redis -p 6379:6379 redis:7-alpine

# 4. 数据库迁移
python -m alembic upgrade head

# 5. 启动服务
start.bat dev
```

启动后访问 http://127.0.0.1:5173

### 服务地址

| 服务 | 地址 |
|------|------|
| 前端应用 | http://127.0.0.1:5173 |
| 后端 API | http://127.0.0.1:8000 |
| API 文档 | http://127.0.0.1:8000/docs |

## 核心功能

- **文档管理**：上传 PDF/DOCX/TXT、标签管理、批量操作、搜索、预览
- **多知识库**：支持创建和管理多个独立知识库
- **RAG 问答**：结合文档上下文的精准回答，SSE 流式输出
- **Tool Calling**：集成 web_search 和 document_lookup 工具
- **多模态**：PDF 视觉解析、图表提取、图像描述生成
- **GraphRAG**：知识图谱构建与关系检索（Neo4j）
- **会话管理**：多轮对话、重命名、置顶、导出

## 环境变量

| 配置项 | 说明 |
|--------|------|
| `DASHSCOPE_API_KEY` | 阿里云 API Key（必填） |
| `DATABASE_URL` | PostgreSQL 连接 |
| `REDIS_URL` | Redis 连接 |
| `NEO4J_URI` | Neo4j 连接（可选，用于 GraphRAG） |

完整配置参考 `.env.example`。

## 常用命令

```bat
start.bat dev          # 启动开发环境
start.bat test         # 运行测试
start.bat health       # 健康检查
start.bat smoke        # 烟雾测试
start.bat acceptance   # 验收测试
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Vite + Element Plus + Pinia |
| 后端 | FastAPI + Pydantic + SQLAlchemy + Uvicorn |
| 任务 | RQ + Redis |
| 数据 | PostgreSQL + pgvector, Neo4j |
| 模型 | Qwen / DashScope + BGE Reranker + Qwen-VL |

## 目录结构

```
├── frontend/      # Vue 3 前端
├── backend/       # FastAPI 后端
├── worker/        # RQ 异步任务
├── scripts/       # 开发脚本
├── data/          # 数据目录
└── .env           # 环境配置
```

## 常见问题

**服务启动失败**

检查 Docker 容器是否运行：
```bash
docker ps
```

启动 PostgreSQL 和 Redis：
```bash
docker run -d --name rag-postgres-pgvector -p 5433:5432 -e POSTGRES_PASSWORD=postgres ankane/pgvector:latest
docker run -d --name rag-redis -p 6379:6379 redis:7-alpine
```

**Neo4j 不可用**

GraphRAG 功能降级，不影响基础文本 RAG 使用。

## 许可证

MIT

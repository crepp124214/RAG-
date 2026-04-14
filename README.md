# RAG 智能文档检索助手

基于 LLM 的企业级智能文档检索与知识问答平台，支持多模态文档解析、知识图谱构建和智能对话。

## 项目概述

本项目从 Streamlit 原型演进为前后端分离的产品级 RAG 系统，支持 PDF/DOCX/TXT 文档上传、语义切片、向量检索、多模态解析、GraphRAG 知识图谱构建、Tool Calling 工具调用和多知识库隔离管理。

## 核心功能

### 📄 文档管理
- 多格式支持：PDF、DOCX、TXT 文件上传
- 异步处理：RQ 任务队列 + Redis，后台完成文档解析、切片、向量生成
- 智能分块：基于语义的文本切片策略
- 标签管理：创建、编辑、删除文档标签，支持批量打标
- 文档搜索：按文件名快速检索
- 文档预览：查看文档详情与处理状态

### 💬 RAG 问答与会话
- SSE 流式输出：实时流式返回问答内容
- 引用卡片：文本引用、视觉引用、图谱引用三种类型
- 会话管理：多轮对话、Markdown 导出、会话置顶与重命名

### 🤖 Tool Calling
- `web_search`：联网搜索外部知识
- `document_lookup`：检索本地文档库
- 流式 Tool Call 输出，实时展示调用状态

### 🎨 多模态 RAG
- PDF 视觉解析：使用 PyMuPDF 提取图表、表格等视觉元素
- 图像描述生成：Qwen-VL 模型生成视觉资产描述
- 统一检索：文本块与视觉块混合向量检索
- BGE Reranker 重排序优化检索结果

### 🕸️ GraphRAG
- 知识图谱构建：Neo4j 图数据库存储实体与关系
- 三元组抽取：自动抽取实体-关系-实体三元组
- 图谱检索降级：Neo4j 不可用时自动降级为纯向量检索

### 🗃️ 多知识库
- 支持创建和管理多个独立知识库
- 文档隔离：文档按知识库分离存储与检索
- 会话隔离：会话按知识库独立管理

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                      Vue 3 SPA                          │
│   Element Plus + Pinia + TypeScript + Vite              │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP / SSE
┌─────────────────────▼───────────────────────────────────┐
│                    FastAPI REST API                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ Chat Routes │  │Doc Routes   │  │ Task Routes │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│  ┌─────────────────────────────────────────────────┐    │
│  │              Service Layer                        │    │
│  │  ChatService │ DocService │ QAService │ ...    │    │
│  └─────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────┐    │
│  │           Repository Layer                       │    │
│  │  DocumentRepo │ SessionRepo │ ChunkRepo │ ...   │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              Infrastructure Layer                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  │
│  │  Vector  │  │   LLM    │  │  Queue   │  │  Graph  │  │
│  │  Store   │  │  Client  │  │ (Redis) │  │ (Neo4j) │  │
│  │(pgvector)│  │(DashScope│  │   RQ    │  │         │  │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 技术栈

| 层级 | 技术选型 |
|------|----------|
| **前端** | Vue 3 + TypeScript + Vite + Element Plus + Pinia |
| **后端** | FastAPI + Pydantic + SQLAlchemy + Alembic + Uvicorn |
| **任务队列** | RQ (Redis Queue) + Redis |
| **数据库** | PostgreSQL + pgvector（向量检索）|
| **图数据库** | Neo4j（GraphRAG 知识图谱）|
| **模型服务** | Qwen（通义千问）+ DashScope Embedding + BGE Reranker + Qwen-VL |
| **文档解析** | PyMuPDF、pdfplumber、python-docx |

## 目录结构

```
├── frontend/                    # Vue 3 单页应用
│   ├── src/
│   │   ├── components/         # Vue 组件
│   │   │   ├── chat/          # 聊天相关组件
│   │   │   └── documents/     # 文档管理组件
│   │   ├── services/           # API 调用层
│   │   ├── stores/            # Pinia 状态管理
│   │   └── types/             # TypeScript 类型定义
│   └── __tests__/             # Vitest 单元测试
│
├── backend/                    # FastAPI 后端
│   ├── api/
│   │   ├── routes/            # API 路由
│   │   └── schemas/           # Pydantic 模型
│   ├── app/
│   │   ├── models/           # SQLAlchemy 模型
│   │   ├── repositories/      # 数据访问层
│   │   ├── services/          # 业务逻辑层
│   │   └── tasks/            # RQ 异步任务
│   └── infrastructure/        # 外部集成
│       ├── database/          # PostgreSQL 连接
│       ├── vector/           # pgvector 向量存储
│       ├── graph/            # Neo4j 图数据库
│       ├── llm/              # LLM 模型调用
│       └── queue/            # Redis 队列
│
├── worker/                     # RQ 异步任务处理器
└── data/                      # 数据存储目录
```

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Docker Desktop

### 启动步骤

```bash
# 1. 配置环境变量
copy .env.example .env
# 编辑 .env 填入 DASHSCOPE_API_KEY

# 2. 启动依赖容器
docker run -d --name rag-postgres-pgvector \
  -p 5433:5432 -e POSTGRES_PASSWORD=postgres \
  ankane/pgvector:latest

docker run -d --name rag-redis \
  -p 6379:6379 redis:7-alpine

# 3. 数据库迁移
python -m alembic upgrade head

# 4. 启动服务
start.bat dev
```

访问 http://127.0.0.1:5173

### 服务地址

| 服务 | 地址 |
|------|------|
| 前端应用 | http://127.0.0.1:5173 |
| 后端 API | http://127.0.0.1:8000 |
| API 文档 | http://127.0.0.1:8000/docs |

## 环境变量

| 配置项 | 说明 |
|--------|------|
| `DASHSCOPE_API_KEY` | 阿里云 API Key（必填） |
| `DATABASE_URL` | PostgreSQL 连接字符串 |
| `REDIS_URL` | Redis 连接字符串 |
| `NEO4J_URI` | Neo4j 连接（可选，用于 GraphRAG）|

完整配置参考 `.env.example`。

## 测试

```bash
# 后端测试（221 个测试用例）
python -m pytest backend/tests/ -v

# 前端测试（64 个测试用例）
cd frontend && npm run test:unit

# 类型检查
npm run typecheck
```

## 项目亮点

- **前后端分离**：Vue 3 SPA + FastAPI REST API，SSE 流式通信
- **异步任务处理**：RQ + Redis 实现文档处理与模型调用的异步化
- **向量检索**：PostgreSQL + pgvector 支持高效语义检索
- **知识图谱**：Neo4j 存储实体关系，GraphRAG 深度查询
- **多模态支持**：PDF 视觉元素提取与描述生成
- **Tool Calling**：web_search + document_lookup 工具集成
- **多知识库**：知识库级数据隔离，支持独立管理

## 许可证

MIT

# 多模态RAG检索问答平台

<div align="center">

**基于 LLM 的智能文档检索与知识问答平台**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

一个从演示到产品的完整 RAG 系统，支持多模态文档解析、知识图谱构建和智能问答

</div>

---

## 🔗 快速导航

### 📦 核心文档
- [设计文档](RAG-design-document.md) - 系统架构与设计理念
- [技术栈说明](tech_stack.md) - 技术选型与依赖
- [实施计划](memory-bank/) - 各阶段实施计划与进度
- [架构文档](memory-bank/architecture.md) - 当前真实架构
- [开发指南](CLAUDE.md) - AI 辅助开发规范

### 📚 阶段文档
- [第一阶段](implementation-plan.md) - 稳定底座与最小可运行产品
- [第二阶段](memory-bank/phase2-implementation-plan.md) - Tool Calling 最小闭环
- [第三阶段](memory-bank/phase3-implementation-plan.md) - PDF 多模态 RAG
- [第四阶段](memory-bank/phase4-implementation-plan.md) - GraphRAG 自动化
- [第五阶段](memory-bank/phase5-implementation-plan.md) - 产品化最小闭环
- [第六阶段](memory-bank/phase6-implementation-plan.md) - 前端界面优化
- [第七阶段](memory-bank/phase7-implementation-plan.md) - 文档与会话管理增强

---

## 🚀 快速开始

### 🐳 一键启动（推荐）

**Windows 环境：**

```bat
# 启动开发环境
start.bat dev

# 查看服务状态
start.bat status

# 停止所有服务
start.bat stop all
```

**或使用 Python 脚本：**

```bash
python run.py dev
```

启动后访问：

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端应用 | http://127.0.0.1:5173 | Vue 3 单页应用 |
| 后端 API | http://127.0.0.1:8000 | FastAPI 服务 |
| API 文档 | http://127.0.0.1:8000/docs | Swagger UI |
| 健康检查 | http://127.0.0.1:8000/api/health | 服务存活状态 |
| 就绪检查 | http://127.0.0.1:8000/api/ready | 依赖就绪状态 |

**默认配置：**
- PostgreSQL: `127.0.0.1:5433` (容器 `rag-postgres-pgvector`)
- Redis: `127.0.0.1:6379` (容器 `rag-redis`)
- Neo4j: `127.0.0.1:7687` (可选，用于 GraphRAG)

### 👨‍💻 开发环境

**前置要求：**
- Python 3.10+
- Node.js 18+
- Docker Desktop (用于 PostgreSQL、Redis、Neo4j)

**启动步骤：**

```bash
# 1. 克隆仓库
git clone https://github.com/crepp124214/RAG-.git
cd RAG智能文档检索助手

# 2. 配置环境变量
copy .env.example .env
# 编辑 .env 填入必要配置

# 3. 启动依赖容器
docker run -d --name rag-postgres-pgvector -p 5433:5432 -e POSTGRES_PASSWORD=postgres ankane/pgvector:latest
docker run -d --name rag-redis -p 6379:6379 redis:7-alpine

# 4. 数据库迁移
python -m alembic upgrade head

# 5. 启动服务
start.bat dev
```

**手动启动各服务：**

```bash
# 后端
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# Worker
python -m worker.main

# 前端
cd frontend && npm run dev -- --host 127.0.0.1 --port 5173
```

---

## ✨ 核心功能

### 📄 文档管理
- **多格式支持**：PDF、DOCX、TXT
- **异步处理**：后台任务队列，支持大文件
- **智能分块**：基于语义的文本切分
- **向量化存储**：使用 DashScope Embedding 生成向量
- **标签管理**：创建、编辑、删除文档标签
- **标签过滤**：按标签快速筛选文档
- **批量操作**：批量删除、批量打标签
- **文档搜索**：按文件名快速搜索
- **文档预览**：查看文档详细信息

### 💬 会话管理
- **多轮对话**：支持上下文连续对话
- **会话重命名**：自定义会话标题
- **会话置顶**：重要会话置顶显示
- **会话搜索**：按标题快速查找会话
- **会话导出**：导出为 Markdown 格式
- **流式输出**：SSE 实时响应

### 🤖 智能问答
- **RAG 检索增强**：结合文档上下文的精准回答
- **Tool Calling**：集成 `web_search` 和 `document_lookup` 工具
- **引用卡片**：展示文本、视觉、图谱三种引用类型

### 🎨 多模态能力
- **PDF 视觉解析**：提取图表、表格等视觉元素
- **图像描述生成**：使用 VLM 模型生成视觉资产描述
- **统一检索**：文本块与视觉块混合检索

### 🕸️ GraphRAG
- **知识图谱构建**：自动抽取实体和关系
- **Neo4j 存储**：高效的图数据库
- **关系检索**：基于图谱的深度查询
- **降级策略**：图谱不可用时自动降级到向量检索

### ✅ 已完成
- [x] 文档上传与异步处理（PDF、DOCX、TXT）
- [x] 文本 RAG 问答与会话管理
- [x] SSE 流式输出
- [x] Tool Calling (`web_search` / `document_lookup`)
- [x] PDF 多模态解析（文本 + 图表）
- [x] 视觉资产提取与描述
- [x] 文本块与视觉块统一检索
- [x] GraphRAG 知识图谱构建
- [x] 三元组抽取与 Neo4j 存储
- [x] 图谱关系检索与降级
- [x] 引用卡片（文本/视觉/图谱）
- [x] 健康检查与就绪检查
- [x] 主链路烟测与验收
- [x] 前端界面优化与响应式布局
- [x] 文档标签管理（创建/编辑/删除标签）
- [x] 文档标签关联与过滤
- [x] 文档搜索与批量操作
- [x] 文档预览功能
- [x] 会话重命名与置顶
- [x] 会话搜索与过滤
- [x] 会话导出为 Markdown

### ⏳ 计划中
- [ ] `python_executor` 工具
- [ ] 独立图谱探索页面
- [ ] `graph_query` 工具
- [ ] 外部知识源补图
- [ ] WebSocket 实时通信
- [ ] 权限系统
- [ ] 多租户支持

---

## ⚙️ 环境配置

### 核心配置

<details>
<summary><b>基础配置</b></summary>

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `APP_ENV` | 运行环境 | `development` |
| `DATABASE_URL` | PostgreSQL 连接 | `postgresql://postgres:postgres@127.0.0.1:5433/rag_assistant` |
| `REDIS_URL` | Redis 连接 | `redis://127.0.0.1:6379/0` |
| `FILE_STORAGE_PATH` | 文件存储路径 | `data/uploads` |

</details>

<details>
<summary><b>模型配置</b></summary>

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `DASHSCOPE_API_KEY` | 阿里云 API Key | - |
| `QWEN_CHAT_MODEL` | 对话模型 | `qwen-plus` |
| `QWEN_VL_MODEL` | 视觉模型 | `qwen-vl-max-latest` |
| `SEARCH_PROVIDER` | 搜索提供商 | `tavily` |
| `SEARCH_API_KEY` | 搜索 API Key | - |

</details>

<details>
<summary><b>多模态配置</b></summary>

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `MULTIMODAL_ENABLED` | 启用多模态 | `true` |
| `MAX_VISUAL_ASSETS_PER_DOCUMENT` | 最大视觉资产数 | `8` |
| `VISUAL_CAPTION_TIMEOUT_SECONDS` | 视觉描述超时 | `12` |

</details>

<details>
<summary><b>GraphRAG 配置</b></summary>

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `NEO4J_URI` | Neo4j 连接 | `bolt://127.0.0.1:7687` |
| `NEO4J_USERNAME` | Neo4j 用户名 | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j 密码 | - |
| `GRAPH_QUERY_LIMIT` | 图查询限制 | `5` |

**注意：** `NEO4J_URI` 未配置时，GraphRAG 自动降级，不影响基础文本 RAG。

</details>

### 快速配置

```bash
# 复制示例配置
copy .env.example .env

# 编辑配置文件
notepad .env
```

完整配置参考：[.env.example](.env.example)

---

## 📖 部署文档

| 文档 | 说明 |
|------|------|
| [快速开始](#-快速开始) | 本地开发环境搭建 |
| [环境配置](#-环境配置) | 环境变量配置指南 |
| [常见问题](#-常见问题) | 故障排查手册 |

---

## 🛠️ 开发工具

### 常用命令

```bat
# 开发
start.bat dev          # 启动开发环境
start.bat status       # 查看服务状态
start.bat stop all     # 停止所有服务

# 测试
start.bat test         # 运行所有测试
start.bat check        # 代码检查（测试+lint+typecheck）
start.bat coverage     # 测试覆盖率

# 质量检查
start.bat lint         # 代码风格检查
start.bat build        # 构建检查

# 验收
start.bat health       # 健康检查
start.bat smoke        # 烟雾测试
start.bat acceptance   # 验收测试
start.bat smoke-flow   # 主链路测试

# 清理
start.bat clean        # 清理临时文件
```

### 推荐验收流程

```bat
# 1. 健康检查
start.bat health

# 2. 启动服务
start.bat dev

# 3. 烟雾测试
start.bat smoke

# 4. 验收测试
start.bat acceptance

# 5. 主链路测试
start.bat smoke-flow

# 6. 代码检查
start.bat check
```

---

## 🏗️ 技术架构

### 技术栈

**前端：**
- Vue 3 + TypeScript
- Vite + Element Plus
- Pinia 状态管理

**后端：**
- FastAPI + Pydantic
- SQLAlchemy + Alembic
- Uvicorn

**异步任务：**
- RQ + Redis

**数据层：**
- PostgreSQL + pgvector
- Neo4j (GraphRAG)

**模型层：**
- Qwen / DashScope
- BGE Reranker
- Qwen-VL

**文档解析：**
- PyPDFLoader + PyMuPDF

### 目录结构

```text
├── frontend/          # Vue 3 前端
├── backend/           # FastAPI 后端
├── worker/            # RQ 异步任务
├── scripts/           # 开发脚本
├── memory-bank/       # 文档与计划
├── data/              # 数据目录
│   └── uploads/       # 上传文件
└── .env               # 环境配置
```

---

## 📊 测试基线

**当前验证通过：**
- 后端测试：`152 passed`
- 前端测试：`19 passed`
- 前端 typecheck：✅ 通过
- 前端 lint：✅ 通过
- Phase 7 端到端测试：✅ 通过

**覆盖范围：**
- 文档上传与处理
- 文本 RAG 问答
- 多模态解析
- GraphRAG 构建
- Tool Calling
- 健康检查与就绪检查
- 主链路端到端测试
- 文档标签管理与过滤
- 会话管理增强功能

---

## 🐛 常见问题

<details>
<summary><b>健康检查失败</b></summary>

**问题：** `health` 显示 `.env missing`

**解决：**
```bash
copy .env.example .env
```

**问题：** `production 环境不得使用 acceptance 模式`

**解决：**
```bash
# 编辑 .env，将 LLM_MODE 改为 production
LLM_MODE=production
```

</details>

<details>
<summary><b>服务启动失败</b></summary>

**问题：** 后端卡在 `Waiting for application startup.`

**原因：** PostgreSQL 或 Redis 未就绪

**解决：**
```bash
# 检查容器状态
docker ps

# 启动 PostgreSQL
docker run -d --name rag-postgres-pgvector -p 5433:5432 -e POSTGRES_PASSWORD=postgres ankane/pgvector:latest

# 启动 Redis
docker run -d --name rag-redis -p 6379:6379 redis:7-alpine
```

**问题：** Worker 提示 `Error 10061 connecting to 127.0.0.1:6379`

**原因：** Redis 未启动

**解决：**
```bash
docker start rag-redis
```

</details>

<details>
<summary><b>就绪检查异常</b></summary>

**问题：** `/api/ready` 返回 `not_ready`

**原因：** 核心依赖不可用

**解决：**
1. 检查 PostgreSQL 连接
2. 检查 Redis 连接
3. 检查文件存储目录

**问题：** `/api/ready` 返回 `degraded`

**原因：** Neo4j 不可用（非致命）

**说明：** 基础文本 RAG 仍可正常使用，GraphRAG 功能降级

</details>

<details>
<summary><b>GraphRAG 不工作</b></summary>

**问题：** 图谱构建失败但文本问答正常

**检查：**
1. `NEO4J_URI` 配置是否正确
2. Neo4j 服务是否启动
3. `/api/ready` 中 `neo4j` 组件状态

**降级说明：** Neo4j 不可用时，系统自动降级为纯文本 RAG，不影响基础功能

</details>

<details>
<summary><b>主链路测试失败</b></summary>

**问题：** `smoke-flow` 提示任务长时间未进入 `READY`

**检查：**
1. Worker 进程是否运行
2. Redis 连接是否正常
3. 模型 API Key 是否配置
4. 上传文档是否支持（PDF/DOCX/TXT）

</details>

---

## 🔄 回滚策略

**配置回滚：**
```bash
# 回退到示例配置
copy .env.example .env
```

**数据库回滚：**
```bash
# 查看当前版本
python -m alembic current

# 回退到指定版本
python -m alembic downgrade <revision>
```

**服务重启：**
```bash
# 停止所有服务
start.bat stop all

# 重新启动
start.bat dev
```

**GraphRAG 降级：**
```bash
# 临时禁用 GraphRAG（编辑 .env）
# NEO4J_URI=  # 注释掉此行
```

---

## 📝 开发约束

- ✅ 先设计，后实现，最后验证
- ✅ 阶段计划先写文档，再执行
- ✅ `progress.md` 按顺序更新，不零散补记
- ✅ `architecture.md` 只记录真实结构
- ✅ 新阶段新增对应的 `implementation-plan` 文件

---

## 📄 许可证

MIT License

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个 Star！**

</div>

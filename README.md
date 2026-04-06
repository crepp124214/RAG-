# RAG 智能文档检索助手

## 项目简介

这是一个从 Streamlit 演示项目逐步重构为产品化系统的 RAG 智能文档检索助手。

当前已完成：

- 第一阶段：稳定底座与最小可运行产品
- 第二阶段：Tool Calling 最小闭环
- 第三阶段：PDF 多模态 RAG 前后端最小闭环
- 第四阶段：GraphRAG 自动化最小闭环

当前技术底座：

- 前端：Vue 3 + Vite + Element Plus + Pinia
- 后端：FastAPI + Pydantic + Uvicorn + SQLAlchemy
- 异步任务：RQ + Redis
- 数据层：PostgreSQL + pgvector
- 图谱层：Neo4j（第四阶段 GraphRAG 本地联调使用）
- 模型层：Qwen / DashScope Embedding / BGE Reranker / Qwen-VL
- 文档解析：PyPDFLoader + PyMuPDF

---

## 当前能力

- 文档上传、异步入库、状态查询与删除
- 文本 RAG 问答、会话持久化、SSE 流式输出
- `web_search` / `document_lookup` Tool Calling
- PDF 视觉资产提取、视觉描述、独立视觉块入库
- 文本块与视觉块统一检索
- 文本块、视觉块与图谱证据的统一检索
- 基于文本块的三元组抽取、Neo4j 图谱入库和关系型问题图检索
- 聊天消息中的文本引用、工具卡片、视觉引用卡片和图谱引用卡片
- 文档详情中的视觉资产摘要与图谱摘要

当前明确未做：

- `python_executor`
- 独立图谱探索页
- `graph_query` 工具
- 外部知识源补图
- WebSocket
- 权限系统
- 多租户

---

## 核心文档

- [RAG-design-document.md](D:\agent开发项目\RAG智能文档检索助手\RAG-design-document.md)
- [tech_stack.md](D:\agent开发项目\RAG智能文档检索助手\tech_stack.md)
- [implementation-plan.md](D:\agent开发项目\RAG智能文档检索助手\implementation-plan.md)
- [memory-bank/phase2-implementation-plan.md](D:\agent开发项目\RAG智能文档检索助手\memory-bank\phase2-implementation-plan.md)
- [memory-bank/phase3-implementation-plan.md](D:\agent开发项目\RAG智能文档检索助手\memory-bank\phase3-implementation-plan.md)
- [memory-bank/phase4-implementation-plan.md](D:\agent开发项目\RAG智能文档检索助手\memory-bank\phase4-implementation-plan.md)
- [memory-bank/progress.md](D:\agent开发项目\RAG智能文档检索助手\memory-bank\progress.md)
- [memory-bank/architecture.md](D:\agent开发项目\RAG智能文档检索助手\memory-bank\architecture.md)
- [CLAUDE.md](D:\agent开发项目\RAG智能文档检索助手\CLAUDE.md)
- [AGENTS.md](D:\agent开发项目\RAG智能文档检索助手\AGENTS.md)

说明：

- `implementation-plan.md`：第一阶段计划
- `phase2-implementation-plan.md`：第二阶段计划
- `phase3-implementation-plan.md`：第三阶段计划
- `phase4-implementation-plan.md`：第四阶段 GraphRAG 计划与本地 Neo4j 联调步骤
- `progress.md`：按顺序记录阶段进展与验收
- `architecture.md`：当前真实结构、调用链和状态边界

---

## 快速开始

Windows 推荐直接使用根目录开发控制台：

```bat
start.bat dev
```

或：

```bat
python run.py dev
```

常用命令：

```bat
start.bat dev
start.bat status
start.bat stop all
start.bat test
start.bat check
start.bat lint
start.bat build
start.bat coverage
start.bat health
start.bat clean
```

如果不在 Windows 环境，也可以直接运行底层命令：

```bash
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
python -m worker.main
cd frontend && npm run dev -- --host 127.0.0.1 --port 5173
python -m pytest backend/tests -p no:cacheprovider
cd frontend && npm run test:unit -- --run
cd frontend && npm run typecheck
cd frontend && npm run lint
```

---

## 环境变量

当前关键后端环境变量：

- `APP_ENV`
- `DATABASE_URL`
- `REDIS_URL`
- `DASHSCOPE_API_KEY`
- `QWEN_CHAT_MODEL`
- `QWEN_VL_MODEL`
- `FILE_STORAGE_PATH`
- `SEARCH_PROVIDER`
- `SEARCH_API_KEY`
- `MULTIMODAL_ENABLED`
- `MAX_VISUAL_ASSETS_PER_DOCUMENT`
- `VISUAL_CAPTION_TIMEOUT_SECONDS`
- `NEO4J_URI`
- `NEO4J_USERNAME`
- `NEO4J_PASSWORD`
- `GRAPH_QUERY_LIMIT`

当前默认值见：

- [\.env.example](D:\agent开发项目\RAG智能文档检索助手\.env.example)
- [backend/.env.example](D:\agent开发项目\RAG智能文档检索助手\backend\.env.example)

其中第三阶段新增的默认值包括：

- `QWEN_VL_MODEL=qwen-vl-max-latest`
- `MULTIMODAL_ENABLED=true`
- `MAX_VISUAL_ASSETS_PER_DOCUMENT=8`
- `VISUAL_CAPTION_TIMEOUT_SECONDS=12`

第四阶段本地 GraphRAG 联调还需要：

- `NEO4J_URI=bolt://127.0.0.1:7687`
- `NEO4J_USERNAME=neo4j`
- `NEO4J_PASSWORD=<本地 Neo4j 密码>`
- `GRAPH_QUERY_LIMIT=5`

完整 Neo4j 启动、上传文档、图检索、降级和删除清理验收步骤见：

- [memory-bank/phase4-implementation-plan.md](D:\agent开发项目\RAG智能文档检索助手\memory-bank\phase4-implementation-plan.md)

---

## 当前验证基线

当前已经实际验证通过：

- 后端测试：`132 passed`
- 前端测试：`17 passed`
- 前端 `typecheck`：通过
- 前端 `lint`：通过

第三阶段已覆盖的关键闭环：

- PDF 多模态入库链支持 `VISUAL_EXTRACTING`
- 视觉资产提取、视觉描述失败降级与独立视觉块入库
- 文本块与视觉块统一检索
- 聊天 `citations` 支持 `source_type / asset_label / preview_available`
- 前端聊天工作台展示视觉引用卡片
- 文档详情展示视觉资产数量

第四阶段已覆盖的自动化闭环：

- 文档入库成功后创建独立 `GRAPH_BUILD` 图谱任务
- 文档详情返回 `has_graph / graph_status / graph_relation_count`
- 三元组抽取服务支持清洗、去空、去重和长度限制
- 图检索与向量检索双路召回，图失败时降级到向量路径
- 聊天 `citations` 支持 `source_type=graph / relation_label / entity_path`
- 前端聊天工作台展示图谱引用卡片
- 文档详情展示图谱状态和关系数量

已完成的第四阶段本地 API 联调：

- 真实 Neo4j 启动与 bolt 连接验证
- 上传文本烟测文档后图谱状态进入 `READY`
- 聊天接口返回 `source_type=graph`、`relation_label`、`entity_path`
- 删除文档后 Neo4j 图关系清理为 `0`
- Neo4j 不可用时文档主状态保持 `READY`，聊天降级为文本引用

已完成的第四阶段前端页面复核：

- `playwright-cli` 页面快照确认聊天工作台显示“图谱引用”
- 页面快照确认图引用显示 `实体路径：系统 -> related_to -> 用户订单`
- `playwright-cli` 控制台错误检查为 `Errors: 0`

---

## 仓库说明

当前主目录：

```text
frontend/
backend/
worker/
scripts/
memory-bank/
```

仍保留但仅作迁移参考：

- `app.py`
- `core/`

---

## 开发约束

- 先设计，后实现，最后验证
- 阶段计划先写文档，再执行计划
- `progress.md` 必须按顺序更新，不能零散补记
- `architecture.md` 只记录真实结构，不写阶段进度
- 新阶段可以新增对应阶段的 `implementation-plan` 文件

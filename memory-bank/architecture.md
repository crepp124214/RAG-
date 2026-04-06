# architecture.md

## 文档说明

本文件只记录当前真实架构、目录职责、关键调用链和状态边界。

使用规则：

- 只写已经落地且可验证的真实结构
- 不写阶段进度、验收结论、下一步建议
- 计划边界看 `implementation-plan.md` 或阶段计划文件
- 进展与验收看 `progress.md`

---

## 当前实现概览

- 当前技术底座：`FastAPI + Vue 3 + PostgreSQL + pgvector + RQ + Redis + Neo4j`
- 当前已落地能力：文档上传、异步处理、向量入库、知识库问答、会话与消息持久化、SSE 流式输出、第二阶段 Tool Calling 最小闭环、第三阶段 PDF 多模态 RAG 最小闭环、第四阶段 GraphRAG 自动化最小闭环
- 当前真实工具：`web_search`、`document_lookup`
- 当前未落地能力：`python_executor`、独立图谱探索页、`graph_query` 工具、外部知识源补图、`Celery`、`Chroma`

---

## 文档职责边界

### `memory-bank/game-design-document.md`

- 作用：记录项目总体设计目标、阶段划分和长期演进方向

### `memory-bank/tech-stack.md`

- 作用：记录技术选型与阶段冻结口径

### `memory-bank/implementation-plan.md`

- 作用：记录第一阶段实施计划

### `memory-bank/phase2-implementation-plan.md`

- 作用：记录第二阶段实施计划

### `memory-bank/phase3-implementation-plan.md`

- 作用：记录第三阶段实施计划

### `memory-bank/phase4-implementation-plan.md`

- 作用：记录第四阶段 GraphRAG 最小闭环计划与本地 Neo4j 联调步骤

### `memory-bank/progress.md`

- 作用：按时间顺序记录阶段进展、验证结果和当前状态

### `memory-bank/architecture.md`

- 作用：记录目录、模块、文件、调用链和状态边界

---

## 目录结构

### `frontend/`

- 作用：Vue 3 前端工作台
- 当前职责：文档上传与跟踪、文档管理、会话列表、聊天工作台、流式问答、工具卡片展示与恢复、视觉引用展示、图谱摘要与图引用展示

### `backend/`

- 作用：FastAPI 后端与业务编排
- 当前职责：API 路由、文档处理编排、文本/视觉/图谱混合检索问答、聊天服务、工具调用编排、结构化日志

### `worker/`

- 作用：RQ Worker 入口
- 当前职责：消费文档异步处理任务与后置图谱构建任务

### `memory-bank/`

- 作用：项目设计、计划、进展和架构记忆区

### `scripts/`

- 作用：统一开发、测试、检查、构建和覆盖率入口

### `core/`

- 作用：旧版 Streamlit 时代的迁移参考代码
- 当前状态：仅作迁移参考，不继续承载长期实现

### `app.py`

- 作用：旧版 Streamlit 入口
- 当前状态：仅作迁移参考

---

## 后端结构

### `backend/main.py`

- 作用：FastAPI 应用入口与应用工厂
- 职责：加载配置、建立数据库与请求上下文、挂载 `/api` 路由、注册异常处理

### `backend/api/`

- 作用：接口协议层
- 当前职责：
  - `routes/`：定义系统、文档、任务、聊天接口
  - `schemas/`：定义请求与响应结构
  - `router.py`：统一聚合路由
  - `error_handlers.py`：统一异常输出

### `backend/app/settings/`

- 作用：统一配置入口
- 当前职责：从环境变量和示例配置读取后端运行参数，包括数据库、Redis、DashScope、文件存储、检索参数、搜索 Provider、第三阶段多模态配置和第四阶段 Neo4j 图谱配置

### `backend/app/models/`

- 作用：SQLAlchemy 领域模型
- 当前事实：
  - `document.py`：文档元数据
  - `task.py`：异步处理任务
  - `chunk.py`：文档分块与向量载体；当前同时承载文本块和视觉块，并保存最小视觉元数据
  - `session.py`：聊天会话
  - `message.py`：聊天消息；当前已持久化 `content`、`citations`、`tool_calls`
- 当前第四阶段新增事实：
  - 文档元数据保存 `graph_status`、`graph_relation_count`
  - 图谱构建使用 `task_type = GRAPH_BUILD` 的独立任务记录
  - 聊天引用可保存 `source_type = graph`、`relation_label`、`entity_path`

### `backend/app/repositories/`

- 作用：数据库访问边界
- 当前职责：隔离文档、任务、会话、消息、分块等读写行为，避免业务服务直接写 SQL

### `backend/app/services/`

- 作用：业务服务层
- 当前职责：
  - 文档解析、视觉资产提取、分块、向量化、图谱抽取、检索、问答
  - 聊天域服务与消息持久化
  - 第二阶段工具门控与工具编排
  - 第四阶段图证据与向量证据双路召回编排

### `backend/app/orchestrators/`

- 作用：业务编排层
- 当前职责：串联文档异步入库和聊天工具调用等跨服务流程

### `backend/app/tools/`

- 作用：第二阶段工具层
- 当前职责：
  - 工具定义与注册
  - 参数校验
  - `web_search`
  - `document_lookup`
  - 工具错误码映射

### `backend/infrastructure/database/`

- 作用：数据库基础设施
- 当前职责：引擎、会话工厂、初始化、Alembic 迁移

### `backend/infrastructure/vector/`

- 作用：向量基础设施
- 当前职责：`pgvector` 字段类型、向量写入、最小相似度查询

### `backend/infrastructure/queue/`

- 作用：Redis 与 RQ 基础设施
- 当前职责：队列连接、入队和 Worker 支撑

### `backend/infrastructure/storage/`

- 作用：文件存储边界
- 当前职责：上传文件保存、路径生成、去重与删除

### `backend/infrastructure/llm/`

- 作用：模型与重排适配层
- 当前职责：Qwen 聊天、Qwen-VL 视觉描述、DashScope Embedding、Reranker、第四阶段三元组抽取，以及第二阶段工具调用协议适配

### `backend/infrastructure/graph/`

- 作用：Neo4j 图谱基础设施边界
- 当前职责：Neo4j 驱动初始化、图关系写入、固定模板图查询、按文档清理图数据
- 约束：不暴露自由 Cypher 生成，不把图查询作为 Tool Calling 工具开放

### `backend/infrastructure/search/`

- 作用：搜索 Provider 适配层
- 当前职责：真实搜索 Provider 与 acceptance/fake Provider 的统一抽象

### `backend/infrastructure/observability/`

- 作用：结构化日志与请求上下文
- 当前职责：统一日志字段、`request_id` 透传和关键链路日志

### `backend/tests/`

- 作用：后端自动化测试
- 当前职责：覆盖配置、数据库、向量、队列、上传、解析、分块、入库、图谱抽取、图任务、检索、问答、聊天、工具调用和 API 契约

---

## 前端结构

### `frontend/src/main.ts`

- 作用：前端应用启动入口

### `frontend/src/App.vue`

- 作用：前端工作台总入口
- 当前职责：组织会话区、聊天区、文档区和任务区

### `frontend/src/config/env.ts`

- 作用：统一读取前端环境变量

### `frontend/src/services/http.ts`

- 作用：统一请求层
- 当前职责：处理标准响应结构、统一错误转换

### `frontend/src/services/documents.ts`

- 作用：文档域接口服务
- 当前职责：上传、详情、任务状态、删除；文档详情包含视觉资产摘要与图谱摘要

### `frontend/src/services/chat.ts`

- 作用：聊天域接口服务
- 当前职责：会话接口、消息接口、同步问答、流式 SSE 解析、工具事件解析、图引用字段解析

### `frontend/src/stores/documents.ts`

- 作用：文档域状态仓库
- 当前职责：跟踪上传文档、轮询任务状态、恢复本地跟踪记录、保存图谱状态与关系数量

### `frontend/src/stores/chat.ts`

- 作用：聊天域状态仓库
- 当前职责：管理会话、消息、流式中间态、文本/视觉/图谱引用信息和工具调用记录

### `frontend/src/components/documents/`

- 作用：文档域组件
- 当前职责：文档管理面板、任务状态摘要、视觉资产摘要、图谱状态摘要

### `frontend/src/components/chat/`

- 作用：聊天域组件
- 当前职责：会话侧边栏与聊天工作台；当前工作台已展示文本引用、视觉引用、图谱引用、工具卡片，并支持刷新恢复

### `frontend/src/tests/`

- 作用：前端自动化测试
- 当前职责：覆盖服务层、状态仓库、聊天工作台、文档交互与流式更新

---

## 关键调用链

### 文档处理链

1. 前端上传文件到 `POST /api/documents/upload`
2. 后端保存文件、创建文档记录和任务记录
3. 后端通过 RQ 入队
4. Worker 执行文本解析、视觉资产提取、分块、向量化、入库
5. 文档与任务状态推进到 `READY` 或 `FAILED`
6. 主入库任务成功后创建独立 `GRAPH_BUILD` 任务
7. 图谱任务只读取文本块抽取三元组并写入 Neo4j
8. 图谱任务成功时更新文档 `graph_status` 与 `graph_relation_count`；失败时不回滚文档主状态

### 知识库问答链

1. 前端发起同步问答或流式问答
2. 聊天接口进入 `ChatService`
3. `RetrievalService` 先执行向量检索，并在关系型问题中尝试图检索
4. 图检索不可用、超时或未命中时自动降级为纯向量路径
5. `qa_service` 执行文本块、视觉块与图证据的统一重排、上下文拼接和模型生成
6. 后端返回答案与文本/视觉/图谱引用
7. 用户消息和助手消息持久化到 `messages`

### GraphRAG 构建链

1. 文档入库主任务成功后创建 `GRAPH_BUILD` 任务
2. `graph_tasks.enqueue_graph_build` 读取该文档 `source_type = text` 的 chunks
3. `GraphTripleExtractionService` 调用图抽取客户端并做本地清洗、去空、去重和长度限制
4. `GraphStore` 使用固定 Neo4j 模板写入 `Entity` 节点与 `RELATED_TO` 关系
5. 图关系保留 `document_id`、`chunk_id`、`page_number` 等来源字段
6. 图任务成功更新文档图谱摘要；图任务失败只更新图谱摘要与任务错误，不改变文档主 `READY`

### 多模态入库链

1. PDF 进入 `DocumentIngestionOrchestrator`
2. 文本解析仍由 `parser_service` 负责
3. 视觉资产提取由 `visual_asset_service` 负责
4. `Qwen-VL` 为每个视觉资产生成描述
5. 视觉描述以独立视觉块进入 `chunks`
6. 文档详情和聊天引用通过 `source_type`、`asset_label`、`preview_available` 暴露多模态信息

### Tool Calling 链

1. 聊天请求进入 `ChatService`
2. 后端先做工具门控，决定允许的工具集合
3. 模型在允许集合内选择直接回答或请求工具调用
4. 工具层校验参数并执行工具
5. 工具结果回灌模型生成最终回答
6. 同步接口返回 `tool_calls`，流式接口发出 `tool_call`、`tool_result`
7. 助手消息持久化时同时写入 `citations` 与 `tool_calls`

---

## 对外接口

### 第一阶段固定接口

- `POST /api/documents/upload`
- `GET /api/documents/{document_id}`
- `GET /api/tasks/{task_id}`
- `DELETE /api/documents/{document_id}`
- `POST /api/chat/sessions`
- `GET /api/chat/sessions`
- `GET /api/chat/sessions/{session_id}/messages`
- `POST /api/chat/query`
- `POST /api/chat/stream`

### 第二阶段接口扩展

- `POST /api/chat/query`
  - 当前新增：`tool_calls`
- `POST /api/chat/stream`
  - 当前新增事件：`tool_call`、`tool_result`
  - 当前 `message_end` 包含本轮工具调用汇总

### 第三阶段接口扩展

- `GET /api/documents/{document_id}`
  - 当前新增：`has_visual_assets`、`visual_asset_count`
- 聊天 `citations`
  - 当前新增：`source_type`、`asset_label`、`preview_available`

### 第四阶段接口扩展

- `GET /api/documents/{document_id}`
  - 当前新增：`has_graph`、`graph_status`、`graph_relation_count`
- `GET /api/tasks/{task_id}`
  - 当前支持返回 `task_type = GRAPH_BUILD` 的图谱任务
- 聊天 `citations`
  - 当前新增：`relation_label`、`entity_path`
  - 图引用使用 `source_type = graph`
- `POST /api/chat/stream`
  - 第四阶段没有新增 SSE 事件类型，图证据继续通过 `citation` 和 `message_end.citations` 返回

---

## 状态边界

### 文档与任务状态

- `UPLOADED`
- `PARSING`
- `VISUAL_EXTRACTING`
- `CHUNKING`
- `EMBEDDING`
- `READY`
- `FAILED`

### 图谱摘要状态

- `NOT_STARTED`
- `PROCESSING`
- `READY`
- `FAILED`

说明：图谱摘要状态不等同于文档主状态。文档主状态进入 `READY` 后，图谱构建失败只影响 `graph_status` 和 `GRAPH_BUILD` 任务，不把文档主状态回退为 `FAILED`。

### 工具调用状态

- `pending`
- `succeeded`
- `failed`

### 工具错误码

- `TOOL_TIMEOUT`
- `TOOL_UNAVAILABLE`
- `TOOL_BAD_ARGUMENTS`
- `TOOL_EXECUTION_ERROR`
- `TOOL_SECURITY_BLOCKED`

---

## 事实来源约定

- 系统长期目标：`game-design-document.md`
- 技术选型与阶段口径：`tech-stack.md`
- 第一阶段计划：`implementation-plan.md`
- 第二阶段计划：`phase2-implementation-plan.md`
- 第三阶段计划：`phase3-implementation-plan.md`
- 第四阶段计划：`phase4-implementation-plan.md`
- 当前进展与验收：`progress.md`
- 当前结构与职责：`architecture.md`

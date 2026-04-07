# RAG 智能文档检索助手重构设计文档

## 1. 文档信息

- 项目名称：RAG 智能文档检索助手
- 文档版本：v1.1
- 文档日期：2026-04-03
- 文档状态：Updated Draft
- 目标：将当前基于 Streamlit 的单体式 RAG Demo 升级为支持 Tool Calling、异步任务、多模态解析，并为 GraphRAG 预留演进路径的产品化系统。

---

## 2. 项目背景

当前系统已经具备基础 RAG 能力：

- 支持 PDF、DOCX、TXT 文档上传与解析
- 支持基础向量检索与问答
- 集成通义千问模型进行生成
- 支持重排、父子文档检索、对话记忆等增强能力

但当前工程形态仍偏向演示版：

- 前后端耦合在 Streamlit 中
- 文档上传后的解析、切块、Embedding、入库基本是同步思路
- 缺少标准 API 层和任务状态跟踪
- 缺少统一工具调用机制
- 多模态与图谱能力尚未产品化

因此，本次重构的重点不是只增加功能，而是先重建清晰、稳定、可扩展的系统边界。

---

## 3. 设计目标

### 3.1 业务目标

- 从“本地文档问答 Demo”升级为“可持续演进的知识助手”
- 让系统既能回答知识库内问题，也能在知识不足时调用外部工具
- 支持逐步扩展图表理解、多模态检索、图谱推理
- 支持多会话、异步文档处理、可观测的后台任务

### 3.2 技术目标

- 前后端彻底解耦
- 统一 API 协议
- 文档处理异步化
- 检索体系统一编排
- 先做简单稳健的底座，再逐步叠加高级能力

### 3.3 非目标

- 本阶段不要求一次性上线 GraphRAG
- 本阶段不追求引入重型基础设施
- 本阶段不要求立即替换所有旧逻辑，可采用渐进迁移

---

## 4. 当前系统评估

结合现有仓库结构，当前系统主要包括：

- `app.py`：Streamlit 主界面
- `core/document_parser.py`：文档解析与切分
- `core/llm_service.py`：模型与 Embedding 接入
- `core/vector_service.py`：向量检索、重排、父子上下文组装
- `core/conversation_memory.py`：对话记忆
- `core/reranker_service.py`：重排服务

### 4.1 当前主要问题

1. 单体结构
   - UI 层和业务编排耦合过深

2. 同步阻塞
   - 文档处理链路不适合大文件和多文件场景

3. 数据层分散且偏 Demo
   - 当前向量检索方案适合原型验证，不是长期最简方案

4. 缺少工具治理
   - 系统不能稳定地在“知识库回答”和“工具调用”之间切换

5. 扩展路径不清晰
   - 多模态与 GraphRAG 没有被纳入明确的阶段规划

---

## 5. 推荐目标架构

重构后的系统建议采用如下分层：

```text
Vue 3 + Element Plus Frontend
        |
        v
FastAPI API Layer
        |
        +--> Upload API
        +--> Chat API
        +--> Session API
        +--> Task API
        |
        v
Application Layer
        |
        +--> Ingestion Orchestrator
        +--> Retrieval Orchestrator
        +--> Tool Calling Orchestrator
        +--> Conversation Service
        |
        v
Async Task Layer
        |
        +--> RQ Workers
        +--> Redis
        |
        v
Data & Model Layer
        |
        +--> PostgreSQL
        +--> pgvector
        +--> Local Storage / Object Storage
        +--> Qwen / Embedding / Reranker
        +--> Qwen-VL (Phase 3)
        +--> Neo4j (Phase 4, Optional)
```

### 5.1 核心思想

- API 层只做协议、认证、流式输出和任务入口
- 检索、工具调用、文档入库由独立编排器负责
- 第一阶段统一使用 PostgreSQL + pgvector，降低组件复杂度
- `Qwen-VL` 和 `Neo4j` 属于后续演进能力，不作为首发依赖

---

## 6. 统一技术栈

这份设计文档以当前已确认方案为准，技术栈与 `tech_stack.md` 保持一致。

## 6.1 前端

- 框架：Vue 3
- 构建工具：Vite
- UI 组件库：Element Plus
- 状态管理：Pinia
- 网络层：Axios
- 流式通信：SSE

## 6.2 后端

- Web 框架：FastAPI
- 数据校验：Pydantic
- 服务运行：Uvicorn
- 异步任务：RQ
- 缓存 / 队列：Redis
- ORM / 数据访问：SQLAlchemy + Pydantic

## 6.3 数据层

- 业务元数据：PostgreSQL
- 向量检索：pgvector
- 文件存储：本地磁盘起步，后续可切换 MinIO / OSS

## 6.4 模型层

- 对话模型：通义千问（Qwen）
- Embedding：DashScope Embedding
- 重排模型：BGE Reranker
- 多模态模型：Qwen-VL（Phase 3 引入）

## 6.5 文档解析

- PDF 主解析：PyMuPDF
- 复杂结构补充解析：pdfplumber

## 6.6 部署

- 开发与测试：Docker Compose

---

## 7. 模块划分设计

建议将后端按职责拆分为：

```text
backend/
  api/
    routes/
    schemas/
    deps/
  app/
    orchestrators/
    services/
    repositories/
    tasks/
    models/
    settings/
  infrastructure/
    llm/
    database/
    vector/
    storage/
    queue/
    observability/
  tests/
```

### 7.1 模块职责

- `api/routes`
  - 暴露 REST API 与 SSE 接口

- `app/orchestrators`
  - 编排聊天、入库、检索、工具调用

- `app/services`
  - 实现文档解析、检索、会话、工具注册等领域逻辑

- `app/tasks`
  - 定义 RQ 任务

- `infrastructure/*`
  - 封装 PostgreSQL、pgvector、Redis、通义模型、对象存储等适配

---

## 8. Tool Calling 机制设计

## 8.1 目标

让系统在本地知识不足时，能够优雅地调用工具，而不是直接编造答案。

## 8.2 首批推荐工具

第一阶段只建议上线低风险、刚需型工具：

1. `web_search`
   - 用途：查询最新公开信息
   - 输入：`query`, `top_k`

2. `document_lookup`
   - 用途：精确查询文档元数据、文档状态、指定文档内容
   - 输入：`document_id`, `filters`, `query`

后续增强工具：

3. `python_executor`
   - 用途：轻量数据计算和代码验证
   - 风险较高，建议第二阶段后再考虑

4. `graph_query`
   - 用途：图谱查询
   - 仅在 GraphRAG 阶段引入

## 8.3 Tool Schema 设计

工具统一使用 JSON Schema 描述，例如：

```json
{
  "name": "web_search",
  "description": "Search recent public web information when local knowledge base is insufficient.",
  "parameters": {
    "type": "object",
    "properties": {
      "query": { "type": "string" },
      "top_k": { "type": "integer", "default": 5 }
    },
    "required": ["query"]
  }
}
```

## 8.4 执行流程

```text
用户提问
  -> Chat Orchestrator 组装上下文
  -> 将问题 + 可用工具 Schema 发给模型
  -> 模型返回：
     A. 直接回答
     B. 工具调用指令
  -> 后端执行工具
  -> 将工具结果回传给模型
  -> 模型生成最终答案
  -> 通过 SSE 返回给前端
```

## 8.5 路由策略

- 包含“今天、最新、最近政策、实时变化”时优先允许 `web_search`
- 包含“某个文档状态、某个文件是否已处理”时允许 `document_lookup`
- `python_executor` 默认关闭，需明确白名单
- `graph_query` 仅在图谱模块完成后开放

## 8.6 失败处理

标准错误码建议：

- `TOOL_TIMEOUT`
- `TOOL_UNAVAILABLE`
- `TOOL_BAD_ARGUMENTS`
- `TOOL_EXECUTION_ERROR`
- `TOOL_SECURITY_BLOCKED`

降级策略：

- 自动重试一次
- 重试失败后回退到知识库内回答
- 明确告知用户答案未包含实时工具结果

---

## 9. 工程架构升级设计

## 9.1 前后端解耦目标

将当前 Streamlit 应用拆分为：

- `frontend/`：Vue 3 前端
- `backend/`：FastAPI 服务
- `worker/`：RQ Worker

## 9.2 API 设计建议

### 文档接口

- `POST /api/documents/upload`
- `GET /api/documents/{document_id}`
- `GET /api/tasks/{task_id}`
- `DELETE /api/documents/{document_id}`

### 会话接口

- `POST /api/chat/sessions`
- `GET /api/chat/sessions`
- `GET /api/chat/sessions/{session_id}/messages`

### 聊天接口

- `POST /api/chat/query`
- `POST /api/chat/stream`

## 9.3 异步任务链路

文档上传后执行如下流水线：

```text
upload accepted
  -> save raw file
  -> parse document
  -> build chunks
  -> embedding
  -> pgvector upsert
  -> mark document ready
```

第一阶段 RQ 任务建议拆分为：

- `parse_document_task`
- `build_chunks_task`
- `embed_and_index_task`
- `finalize_document_task`

第二阶段可以按需增加：

- `extract_visual_assets_task`
- `generate_image_caption_task`

第四阶段再增加：

- `extract_triples_task`
- `build_graph_task`

## 9.4 状态机设计

文档状态建议定义为：

- `UPLOADED`
- `PARSING`
- `CHUNKING`
- `EMBEDDING`
- `READY`
- `FAILED`

若进入多模态与图谱阶段，可新增：

- `VISUAL_EXTRACTING`
- `GRAPH_BUILDING`

---

## 10. 前端设计

## 10.1 目标能力

- 现代化聊天体验
- 上传进度与任务状态展示
- 历史会话管理
- 文档管理页
- 引用来源和工具调用记录展示

## 10.2 页面结构建议

### 主工作台

- 左侧：知识库与历史会话
- 中间：聊天主窗口
- 右侧：引用片段、工具调用记录、来源卡片

### 文档管理页

- 文档列表
- 状态筛选
- 任务进度
- 文档详情与片段预览

### 扩展页

- 多模态资产页（Phase 3）
- 图谱探索页（Phase 4）

## 10.3 Pinia Store 建议

- `useSessionStore`
- `useChatStore`
- `useDocumentStore`
- `useTaskStore`

GraphRAG 上线后再增加：

- `useKnowledgeGraphStore`

## 10.4 SSE 事件建议

- `message_start`
- `token`
- `citation`
- `tool_call`
- `tool_result`
- `message_end`
- `error`

---

## 11. 多模态文档解析设计

本能力不作为第一阶段必做功能，而是第三阶段增强项。

## 11.1 目标

增强系统对 PDF 中图表、图片、扫描页和复杂版式内容的理解能力。

## 11.2 解析流程

1. 使用 `PyMuPDF` 提取文本块与图片
2. 必要时使用 `pdfplumber` 补充复杂版面解析
3. 为图片生成资产记录
4. 调用 `Qwen-VL` 生成图像描述
5. 将“图像描述 + 周边正文 + 页码 + 坐标”组装为多模态 chunk
6. 写入 PostgreSQL + pgvector

## 11.3 风险点

- 图文定位难
- 成本与时延增加明显
- 大文档会拉长入库时间

因此建议：

- 第一阶段先只做文本 RAG
- 第三阶段再补多模态

---

## 12. GraphRAG 设计

GraphRAG 明确作为第四阶段能力，不进入第一阶段首发范围。

## 12.1 目标

补足向量检索在全局总结、跨段关系归纳、多实体推理上的弱项。

## 12.2 引入时机

仅当以下场景成为核心需求时引入：

- 跨文档关系归纳
- 实体网络探索
- 复杂合作关系与链路分析

## 12.3 引入方案

第四阶段增加：

- Neo4j
- 实体抽取与关系抽取
- 三元组归一化
- 图谱检索接口
- 图谱与向量的双路召回
- 文档入库成功后的异步图谱构建任务

第四阶段默认口径：

- 图谱来源只来自本地已入库文档
- 初版只基于文本块构图，不纳入视觉描述块
- 图检索作为检索编排内部能力，不暴露为独立工具
- 不在第四阶段首发独立图谱探索页

## 12.4 双路召回架构

```text
User Query
  -> Query Understanding
     -> Vector Retrieval (PostgreSQL + pgvector)
     -> Graph Retrieval (Neo4j, Optional)
  -> Merge Context
  -> Rerank
  -> LLM Answer Generation
```

## 12.5 风险点

- 三元组抽取噪声较大
- 图模式设计需要多轮调优
- Cypher 自动生成存在安全与幻觉风险

---

## 13. 检索编排设计

建议引入统一的 Retrieval Orchestrator。

## 13.1 查询类型

1. 事实定位型问题
   - 向量检索为主

2. 时效性问题
   - Tool Calling + RAG

3. 图表理解型问题
   - 多模态检索（Phase 3）

4. 全局关系型问题
   - GraphRAG + 向量检索（Phase 4）

## 13.2 查询计划输出

```json
{
  "need_vector": true,
  "need_tool_call": false,
  "need_multimodal": false,
  "need_graph": false,
  "top_k": 8
}
```

---

## 14. 数据模型设计

建议统一使用 PostgreSQL 管理业务元数据，并通过 pgvector 承担第一阶段向量检索。

核心表建议：

- `users`
- `sessions`
- `messages`
- `documents`
- `document_tasks`
- `chunks`
- `tool_call_logs`
- `retrieval_logs`

---

## 15. 安全设计

## 15.1 API 安全

- JWT 或 Session Token
- 上传大小限制
- 文档类型白名单
- 接口限流

## 15.2 工具安全

- 工具白名单注册
- 工具调用审计
- 高风险工具默认关闭

## 15.3 数据安全

- 文档存储访问控制
- 敏感日志脱敏
- 外部搜索结果不过度持久化

---

## 16. 可观测性设计

统一记录：

- request_id
- session_id
- document_id
- task_id
- tool_name
- model_name
- latency_ms
- error_code

建议采集：

- 文档解析耗时
- Embedding 耗时
- 首 token 延迟
- 工具调用成功率
- 检索耗时

---

## 17. 部署设计

## 17.1 开发环境

建议通过 Docker Compose 启动：

- `frontend`
- `backend`
- `worker`
- `redis`
- `postgres`

## 17.2 生产环境建议

- 前端：Nginx + 静态托管
- 后端：FastAPI + Uvicorn/Gunicorn
- Worker：独立 RQ Worker
- Redis：托管版或高可用实例
- PostgreSQL：主业务数据库，同时承载 pgvector

仅在第四阶段引入：

- Neo4j

## 17.3 环境变量

- `APP_ENV`
- `API_PREFIX`
- `DASHSCOPE_API_KEY`
- `QWEN_CHAT_MODEL`
- `QWEN_VL_MODEL`
- `EMBEDDING_MODEL`
- `REDIS_URL`
- `DATABASE_URL`
- `FILE_STORAGE_PATH`

GraphRAG 阶段再增加：

- `NEO4J_URI`
- `NEO4J_USERNAME`
- `NEO4J_PASSWORD`

---

## 18. 分阶段实施路线

## Phase 1：稳定底座

目标：

- 完成前后端解耦
- 建立 FastAPI + Vue 3 + PostgreSQL + pgvector + RQ + Redis 基础架构
- 打通文档上传、异步入库、基础聊天

交付：

- 标准 API
- 异步任务状态流转
- Vue 工作台

## Phase 2：Tool Calling

目标：

- 引入统一工具注册与调度机制
- 先支持 `web_search` 与 `document_lookup`

交付：

- Tool Schema 管理
- 工具执行编排器
- 工具日志与失败降级

## Phase 3：多模态 RAG

目标：

- 支持 PDF 图片/图表抽取
- 接入 Qwen-VL
- 建立混合 chunk 检索

交付：

- 视觉资产提取流程
- 图片描述缓存
- 多模态检索

## Phase 4：GraphRAG

目标：

- 引入 Neo4j
- 构建三元组抽取与图谱检索能力

交付：

- 图谱入库
- 图谱查询
- 双路召回与重排
- 文档图谱摘要
- 聊天图引用返回

## Phase 5：稳定性与产品化

目标：

- 完成稳定性与产品化最小闭环
- 让现有四阶段能力更容易启动、检查、部署、排错和验收
- 第一轮只做运行检查、健康/就绪检查、配置治理、部署验收和最低可观测性

交付：

- `phase5-implementation-plan.md`
- 健康检查与就绪检查口径
- 本地 / 小规模部署验收清单
- 配置校验与灰度配置说明
- 基于现有结构化日志的最低可观测性说明
- smoke/check 脚本规划
- 灰度配置能力

边界：

- 第五阶段第一轮不做鉴权、登录、多租户
- 不引入 Kubernetes、完整 CI/CD 平台、Prometheus / Grafana 正式接入
- 不新增 RAG 能力，不新增图谱探索页，不暴露 `graph_query` 工具
- 继续优先采用 Docker Compose / Windows 脚本路线

---

## 19. 风险与难点总结

### 19.1 Tool Calling

- 模型工具选择不稳定
- 外部工具失败率不可控
- `python_executor` 安全风险高

### 19.2 异步工程化

- RQ 任务状态与前端轮询配合仍需设计清楚
- SSE 断线重连和会话恢复需要单独处理

### 19.3 多模态

- 图文定位难
- 成本和时延上升明显

### 19.4 GraphRAG

- 三元组抽取噪声较大
- 图模型和查询模板需要持续调优

---

## 20. 成功标准

当系统满足以下条件时，可视为本轮重构成功：

- 文档上传不再阻塞前端
- 聊天接口支持 SSE
- 当知识库不足时能正确触发工具调用
- 第一阶段无需依赖重型基础设施即可稳定运行
- 后续能够平滑扩展多模态与 GraphRAG

---

## 21. 后续建议

这份文档现在已经与 `tech_stack.md` 对齐。下一步最合适的是继续输出一份实施计划文档，拆清楚：

1. 目录结构迁移
2. PostgreSQL 表设计
3. pgvector 索引方案
4. FastAPI API 清单
5. RQ 任务拆分
6. Vue 前端页面与状态设计

---

## 22. 本文档关键结论

- 第一阶段技术底座以 `FastAPI + Vue 3 + PostgreSQL + pgvector + RQ + Redis` 为核心
- `Qwen-VL` 是第三阶段增强项，不是首发依赖
- `Neo4j / GraphRAG` 是第四阶段能力，不应提前加重系统复杂度
- 最优路径是先做简单、稳健、可维护的产品底座，再逐步叠加 Tool Calling、多模态和 GraphRAG


# progress.md

## 文档说明

本文件用于记录《implementation-plan.md》中各步骤的完成情况、验证结果和备注信息。

使用规则：

- 每完成一个已验证通过的实施步骤，必须更新本文件
- 未完成或未验证通过的步骤，不得标记为完成
- 如果步骤实现了但验证失败，必须明确记录失败原因
- 如果计划发生调整，必须同时更新实施计划与本文件

---

## 当前阶段

- 当前阶段：第一阶段最小可运行产品
- 当前目标：完成基础底座，不提前实现 Tool Calling、多模态、GraphRAG

---

## 进度总览

- 总状态：进行中
- 已完成步骤数：28
- 当前进行步骤：无
- 下一步建议：完成第一阶段集成验收

## 最新补充：步骤 23-28

- 步骤 23 已完成：前端文档上传流程已接入，支持上传、失败提示、任务状态恢复和刷新后继续追踪。
- 步骤 24 已完成：前端文档管理页已落地，展示文档列表、文档详情、任务摘要并支持硬删除。
- 步骤 25 已完成：前端聊天工作台已接入会话列表、消息历史、引用展示和新建会话能力。
- 步骤 26 已完成：前端已通过 `fetch + SSE` 解析实现流式问答，支持中途失败、结束收敛和再次发问。
- 步骤 27 已完成：前后端自动化测试已补齐并通过，当前主链路覆盖上传、文档管理、聊天、流式更新和后端核心服务。
- 步骤 28 已完成：后端已补充结构化日志、请求标识透传和关键链路日志，可关联请求、文档、任务和会话。
- 验证结果：`cmd /c npm run build`、`cmd /c npm run test:unit -- --run` 和 `python -m pytest backend/tests -p no:cacheprovider` 均通过；当前后端测试结果为 `87 passed`。

---

## 状态说明

- `未开始`：尚未进入实施
- `进行中`：正在实施，尚未完成全部验证
- `已完成`：实现完成且验证通过
- `已阻塞`：存在外部依赖或关键问题，暂时无法推进
- `已跳过`：明确决定本阶段不做，并记录原因

---

## 步骤记录模板

后续新增记录时，按下面格式填写：

### 步骤 X：步骤名称

- 状态：
- 完成时间：
- 对应计划：
- 实现内容：
- 验证结果：
- 备注：

---

## 当前实施计划步骤清单

### 步骤 1：确认第一阶段范围与冻结边界

- 状态：已完成
- 完成时间：2026-04-03
- 对应计划：`implementation-plan.md`
- 实现内容：冻结了第一阶段范围与禁止项；在 `implementation-plan.md` 中补充了“第一阶段冻结口径”和“第一阶段关键默认值”；在 `tech-stack.md` 中补充了“第一阶段冻结实现口径”；明确了单用户、无登录、无鉴权、无 `users` 表、`SQLAlchemy + Alembic`、重复上传提示已存在、硬删除、一文档多任务、会话标题自动截断、测试工具链、分块默认值、检索默认值、SSE 第一阶段事件集合以及旧 `core/` 的迁移策略。
- 验证结果：已由用户人工验证并确认通过；当前第一阶段范围、默认实现口径和禁止项在 `memory-bank` 内已形成统一口径；后续开发者无需再为高影响决策做二次选型。
- 备注：按用户要求，`game-design-document.md` 保持总体设计方案定位，不承载第一阶段冻结细节；第一阶段冻结事实来源以 `implementation-plan.md` 和 `tech-stack.md` 为准；在用户确认验证通过前，未开始第 2 步，也未提前记录完成状态。

### 步骤 2：建立新目录骨架

- 状态：已完成
- 完成时间：2026-04-03
- 对应计划：`implementation-plan.md`
- 实现内容：创建了 `frontend/`、`backend/`、`worker/` 三段式目录；在 `backend/` 下创建了 `api`、`app`、`infrastructure`、`tests` 四层结构；在 `api/` 下创建了 `routes`、`schemas`、`deps`；在 `app/` 下创建了 `orchestrators`、`services`、`repositories`、`tasks`、`models`、`settings`；在 `infrastructure/` 下创建了 `llm`、`database`、`vector`、`storage`、`queue`、`observability`；使用 `.gitkeep` 固定空目录结构以便版本控制。
- 验证结果：已由用户人工验证并确认通过；新目录层级与实施计划一致；旧 `app.py` 与 `core/` 均保留，未被误删或改造；本轮未进入第 3 步，也未提前创建配置实现、FastAPI 应用或前端工程内容。
- 备注：当前仅完成结构骨架，不代表具体业务模块已实现；后续开发必须继续遵循“旧 `core/` 作为迁移参考，新能力优先落到新架构目录”的约束。

### 步骤 3：建立统一配置体系

- 状态：已完成
- 完成时间：2026-04-03
- 对应计划：`implementation-plan.md`
- 实现内容：新增了根目录 [`.env.example`](C:\Users\qwer\.codex\worktrees\e514\RAG智能文档检索助手\.env.example)、[`backend/.env.example`](C:\Users\qwer\.codex\worktrees\e514\RAG智能文档检索助手\backend\.env.example) 和 [`frontend/.env.example`](C:\Users\qwer\.codex\worktrees\e514\RAG智能文档检索助手\frontend\.env.example) 作为第一阶段统一配置示例；新增了后端统一配置入口 [`backend/app/settings/config.py`](C:\Users\qwer\.codex\worktrees\e514\RAG智能文档检索助手\backend\app\settings\config.py) 和导出文件 [`backend/app/settings/__init__.py`](C:\Users\qwer\.codex\worktrees\e514\RAG智能文档检索助手\backend\app\settings\__init__.py)；新增了前端 API 地址读取入口 [`frontend/src/config/env.ts`](C:\Users\qwer\.codex\worktrees\e514\RAG智能文档检索助手\frontend\src\config\env.ts)；新增了配置加载测试 [`backend/tests/test_config.py`](C:\Users\qwer\.codex\worktrees\e514\RAG智能文档检索助手\backend\tests\test_config.py)；同步更新了 [`README.md`](C:\Users\qwer\.codex\worktrees\e514\RAG智能文档检索助手\README.md) 的配置说明。
- 验证结果：已由用户人工验证并确认通过；本地执行 `python -m pytest backend/tests/test_config.py -p no:cacheprovider` 通过，验证了“完整配置可加载、缺少关键配置时报错、分块参数关系校验生效”三类行为。
- 备注：本轮只完成统一配置体系，没有提前进入 FastAPI 应用初始化；后端配置当前依赖 `python-dotenv` 读取 `.env` 文件，旧 `core/` 中分散读取环境变量的方式后续将逐步迁移到统一配置入口。

### 步骤 4：搭建 FastAPI 基础应用

- 状态：已完成
- 完成时间：2026-04-03
- 对应计划：`implementation-plan.md`
- 实现内容：新增了应用入口 [`backend/main.py`](C:\Users\qwer\.codex\worktrees\e514\RAG智能文档检索助手\backend\main.py)，实现了 `create_app` 工厂、`lifespan` 配置加载和 `/api` 路由挂载；新增了统一异常定义 [`backend/app/exceptions.py`](C:\Users\qwer\.codex\worktrees\e514\RAG智能文档检索助手\backend\app\exceptions.py)、统一响应结构 [`backend/api/schemas/response.py`](C:\Users\qwer\.codex\worktrees\e514\RAG智能文档检索助手\backend\api\schemas\response.py) 和异常处理注册 [`backend/api/error_handlers.py`](C:\Users\qwer\.codex\worktrees\e514\RAG智能文档检索助手\backend\api\error_handlers.py)；新增了健康检查路由 [`backend/api/routes/system.py`](C:\Users\qwer\.codex\worktrees\e514\RAG智能文档检索助手\backend\api\routes\system.py)、路由聚合 [`backend/api/router.py`](C:\Users\qwer\.codex\worktrees\e514\RAG智能文档检索助手\backend\api\router.py) 和文档/任务/聊天预留路由模块；新增了接口测试 [`backend/tests/test_app.py`](C:\Users\qwer\.codex\worktrees\e514\RAG智能文档检索助手\backend\tests\test_app.py)；同步补充了 [`requirements.txt`](C:\Users\qwer\.codex\worktrees\e514\RAG智能文档检索助手\requirements.txt) 中的 FastAPI、Pydantic、Uvicorn 依赖声明。
- 验证结果：已由用户人工验证并确认通过；本地执行 `python -m pytest backend/tests/test_config.py backend/tests/test_app.py -p no:cacheprovider` 通过，验证了健康检查接口、404 标准错误响应、`/docs` 文档页可用、业务异常与未处理异常统一转换这四类行为。
- 备注：本轮只完成 FastAPI 基础应用骨架，不包含数据库接入、业务路由实现和前端工程初始化；为避免导入期直接失败，运行时配置加载放到了 `lifespan` 阶段。

### 步骤 5：搭建 Vue 3 基础前端

- 状态：已完成
- 完成时间：2026-04-03
- 对应计划：`implementation-plan.md`
- 实现内容：初始化了 `Vue 3 + Vite + Element Plus + Pinia` 前端工程；新增了 [`frontend/package.json`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\frontend\package.json)、[`frontend/index.html`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\frontend\index.html)、[`frontend/tsconfig.json`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\frontend\tsconfig.json)、[`frontend/vite.config.ts`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\frontend\vite.config.ts) 和 [`frontend/package-lock.json`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\frontend\package-lock.json)；新增了应用入口 [`frontend/src/main.ts`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\frontend\src\main.ts)、页面骨架 [`frontend/src/App.vue`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\frontend\src\App.vue) 和类型声明 [`frontend/src/vite-env.d.ts`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\frontend\src\vite-env.d.ts)；新增了统一请求层 [`frontend/src/services/http.ts`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\frontend\src\services\http.ts)、健康检查服务 [`frontend/src/services/system.ts`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\frontend\src\services\system.ts) 和系统状态仓库 [`frontend/src/stores/system.ts`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\frontend\src\stores\system.ts)；工作台页面已预留会话列表、聊天区、文档管理区和任务状态区，并接入后端 `/api/health` 显示加载中、成功和失败提示；新增了前端测试 [`frontend/src/tests/api.spec.ts`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\frontend\src\tests\api.spec.ts)、[`frontend/src/tests/setup.ts`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\frontend\src\tests\setup.ts) 和 [`frontend/src/__tests__/App.spec.ts`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\frontend\src\__tests__\App.spec.ts)；同时更新了 [`.gitignore`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\.gitignore) 以忽略前端依赖和构建产物。
- 验证结果：已由用户人工验证并确认通过；在当前工作区补装前端依赖后，本地执行 `cmd /c npm run build`、`cmd /c npm run test:unit -- --run` 和 `python -m pytest backend/tests/test_app.py -p no:cacheprovider` 均通过；验证了前端工程可构建、单元测试通过、基础工作台可渲染，且与后端健康检查接口联通正常。
- 备注：本步初次验证失败的根因不是前端代码逻辑错误，而是当前工作区尚未执行 `frontend` 目录的 `npm install`，导致 `vite` 和 `vitest` 命令不可用；补装依赖后重新验证通过。本步只完成前端工程骨架、基础布局、健康检查联通和统一请求封装，未进入文档上传、会话接口、真实聊天链路或数据库接入。

### 步骤 6：接入 PostgreSQL

- 状态：已完成
- 完成时间：2026-04-03
- 对应计划：`implementation-plan.md`
- 实现内容：新增了 SQLAlchemy 数据模型基座 [`backend/app/models/base.py`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\backend\app\models\base.py) 以及第一阶段最小业务模型 [`document.py`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\backend\app\models\document.py)、[`task.py`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\backend\app\models\task.py)、[`session.py`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\backend\app\models\session.py)、[`message.py`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\backend\app\models\message.py)、[`chunk.py`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\backend\app\models\chunk.py)；新增了数据库基础设施 [`backend/infrastructure/database/connection.py`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\backend\infrastructure\database\connection.py)、[`session.py`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\backend\infrastructure\database\session.py)、[`initializer.py`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\backend\infrastructure\database\initializer.py)；新增了 Alembic 骨架和首个迁移 [`alembic.ini`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\alembic.ini)、[`backend/infrastructure/database/migrations/env.py`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\backend\infrastructure\database\migrations\env.py)、[`backend/infrastructure/database/migrations/versions/20260403_000001_create_phase_one_tables.py`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\backend\infrastructure\database\migrations\versions\20260403_000001_create_phase_one_tables.py)；更新了 [`backend/main.py`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\backend\main.py) 以在应用启动期建立数据库引擎、校验连接并挂载会话工厂；更新了 [`requirements.txt`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\requirements.txt) 并新增数据库测试 [`backend/tests/test_database.py`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\backend\tests\test_database.py)。
- 验证结果：已由用户人工验证并确认通过；本地执行 `python -m pytest backend/tests/test_database.py backend/tests/test_app.py backend/tests/test_config.py -p no:cacheprovider` 通过，验证了数据库连接检查、首批表创建、最小模型插入与查询、Alembic 骨架存在以及 FastAPI 启动期数据库初始化链路。
- 备注：本步只完成 PostgreSQL 接入底座与关系型表结构，不包含 `pgvector` 字段、向量索引或检索逻辑；测试中使用工作区内的 SQLite 临时数据库文件替代系统临时目录，以规避当前 Windows 环境下 `pytest` 默认临时目录权限问题；生产目标数据库仍然是 PostgreSQL。

### 步骤 7：接入 pgvector

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：为 [`backend/app/models/chunk.py`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\backend\app\models\chunk.py) 新增了 `embedding` 向量字段；新增了向量类型与最小存取模块 [`backend/infrastructure/vector/types.py`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\backend\infrastructure\vector\types.py)、[`backend/infrastructure/vector/store.py`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\backend\infrastructure\vector\store.py) 和 [`backend/infrastructure/vector/__init__.py`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\backend\infrastructure\vector\__init__.py)；新增了第 7 步迁移脚本 [`backend/infrastructure/database/migrations/versions/20260403_000002_add_chunk_embedding.py`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\backend\infrastructure\database\migrations\versions\20260403_000002_add_chunk_embedding.py)；更新了 [`backend/infrastructure/database/initializer.py`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\backend\infrastructure\database\initializer.py) 以在 PostgreSQL 环境准备 `vector` 扩展；更新了 [`requirements.txt`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\requirements.txt) 并新增/扩展了 [`backend/tests/test_vector.py`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\backend\tests\test_vector.py) 和 [`backend/tests/test_database.py`](C:\Users\qwer\.codex\worktrees\23c5\RAG智能文档检索助手\backend\tests\test_database.py)。
- 验证结果：已由用户人工验证并确认通过；本地执行 `python -m pytest backend/tests/test_database.py backend/tests/test_vector.py backend/tests/test_app.py backend/tests/test_config.py -p no:cacheprovider` 通过，验证了向量字段已落到分块模型、最小向量写入与相似度查询可用、空数据集查询返回空结果，以及现有 FastAPI 与配置测试未回归。
- 备注：本步严格限制在 `pgvector` 接入底座，只完成向量列、最小存取和相似度查询，不包含向量化服务、Embedding 调用、重排逻辑或正式检索编排；PostgreSQL 路径使用 `pgvector`，SQLite 仅作为测试回退到 JSON 存储，避免本地自动化测试被数据库扩展依赖阻塞。

### 步骤 8：接入 Redis 与 RQ

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：已完成 Redis 连接、RQ 队列封装、Worker 入口、任务入队与任务状态查询链路，为后续文档异步入库提供正式基础设施。
- 验证结果：后端自动化测试已覆盖最小任务执行、成功任务状态和失败任务状态。
- 备注：第一阶段异步能力固定为 `RQ + Redis`，未引入 Celery 或其他队列系统。

### 步骤 9：建立文件存储规则与文档元数据模型

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：已建立上传文件落盘规则、文档记录与任务记录创建流程，并限制在第一阶段最小元数据范围内。
- 验证结果：后端自动化测试已覆盖磁盘落盘、文档记录、任务记录、非法文件和空文件。
- 备注：重复上传采用“提示已存在，不重复入库”策略。

### 步骤 10：实现文档上传接口

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：已落地 `POST /api/documents/upload`，支持 PDF、DOCX、TXT，返回 `document_id` 与 `task_id`，并将耗时处理交给后台队列。
- 验证结果：后端自动化测试已覆盖合法上传、非法类型上传和重复上传场景。
- 备注：上传请求线程只负责保存和入队，不同步做解析与入库。

### 步骤 11：实现文档状态与任务状态接口

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：已落地文档详情接口和任务详情接口，返回与后台任务一致的状态、失败原因和最小必要元数据。
- 验证结果：后端自动化测试已覆盖处理中、完成、失败三类状态读取。
- 备注：前端刷新恢复能力依赖这两个接口，因此它们已成为文档域的正式查询事实来源。

### 步骤 12：迁移旧解析逻辑到新服务层

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：已从旧 `core/` 中复用文本解析能力，并通过新服务层包一层统一输出结构。
- 验证结果：后端自动化测试已覆盖 TXT、PDF、DOCX 成功解析和损坏文档失败路径。
- 备注：本步只迁移文本链路，没有引入多模态解析。

### 步骤 13：实现文本分块服务

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：已实现段落优先的统一分块策略，默认 `chunk_size=800`、`chunk_overlap=150`，并保留 `document_id`、`page_number`、`chunk_index`、`source_type` 等元数据。
- 验证结果：后端自动化测试已覆盖稳定分块、短文档分块和空文本保护。
- 备注：分块策略已冻结为第一阶段默认值，后续调整应同步更新配置和测试。

### 步骤 14：实现向量化与入库服务

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：已接入 DashScope Embedding，将分块文本、元数据和向量写入 PostgreSQL + pgvector。
- 验证结果：后端自动化测试已覆盖向量入库成功和 Embedding 失败转 `FAILED`。
- 备注：本步只做向量化与入库，不扩展到工具调用或多模态向量化。

### 步骤 15：串联完整异步入库流水线

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：已用 RQ 串联解析、分块、向量化、状态更新和失败回写，形成完整异步入库流水线。
- 验证结果：后端自动化测试已覆盖成功链路、阶段状态推进和中途失败停止后续处理。
- 备注：文档任务状态严格遵守 `UPLOADED -> PARSING -> CHUNKING -> EMBEDDING -> READY/FAILED`。

### 步骤 16：实现文档删除接口

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：已实现文档硬删除，删除文档元数据、关联分块和原始文件。
- 验证结果：后端自动化测试已覆盖已存在文档删除和不存在文档报错。
- 备注：第一阶段采用硬删除，没有引入软删除字段。

### 步骤 17：实现基础检索服务

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：已实现基于 pgvector 的召回、`top_k=12` 候选检索和 `BGE Reranker` 的 `top_n=5` 重排，并输出引用所需字段。
- 验证结果：后端自动化测试已覆盖命中、空命中和重排链路。
- 备注：当前检索仍然严格限制在第一阶段知识库内，不接图谱或外部搜索。

### 步骤 18：实现基础问答编排服务

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：已实现问题输入、检索、上下文拼接、Qwen 调用和答案生成的基础问答编排服务。
- 验证结果：后端自动化测试已覆盖知识库命中回答、空命中保守回复和模型失败路径。
- 备注：第一阶段不启用 Tool Calling，未命中时宁可少答也不强答。

### 步骤 19：实现会话创建与消息持久化

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：已实现会话创建、首轮问题自动生成标题和问答消息持久化。
- 验证结果：后端自动化测试已覆盖标题生成、消息落库和失败回滚。
- 备注：异常时不会留下半条助手消息。

### 步骤 20：实现会话列表与消息列表接口

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：已实现会话列表和消息列表接口，按最近活跃排序并返回第一阶段最小必要字段。
- 验证结果：后端自动化测试已覆盖空列表、多会话排序和不存在会话错误。
- 备注：列表接口不做复杂筛选。

### 步骤 21：实现同步聊天接口

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：已实现 `POST /api/chat/query`，联动知识库问答、消息持久化和引用返回。
- 验证结果：后端自动化测试已覆盖正常问答、空问题和非法会话。
- 备注：同步接口和流式接口共用同一套聊天域服务。

### 步骤 22：实现 SSE 流式聊天接口

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：已实现 `POST /api/chat/stream`，固定输出 `message_start`、`citation`、`token`、`message_end`、`error` 五类事件。
- 验证结果：后端自动化测试已覆盖流式成功、异常中断和流式结束后完整消息持久化。
- 备注：为遵守第一阶段边界，本步不引入 WebSocket。

### 步骤 23：实现前端文档上传流程

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：前端已接入文档上传、失败提示、任务状态恢复和刷新后继续追踪；通过本地持久化记录 `document_id/task_id` 恢复已跟踪文档。
- 验证结果：前端构建和单元测试通过；上传成功、失败和刷新恢复链路已验证。
- 备注：为遵守既定接口边界，前端没有擅自新增 `GET /api/documents`。

### 步骤 24：实现前端文档管理页

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：已完成文档列表、文档详情、任务摘要和删除操作。
- 验证结果：前端构建和单元测试通过；文档查看与删除行为已验证。
- 备注：删除后会同步清理本地已跟踪文档记录。

### 步骤 25：实现前端聊天工作台

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：已完成会话列表、消息区、输入区、引用展示和新建会话。
- 验证结果：前端构建和单元测试通过；会话切换、历史消息加载和引用展示行为已验证。
- 备注：聊天域状态统一由 `chat` 仓库管理。

### 步骤 26：实现前端流式问答体验

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：已完成基于 `fetch + SSE` 的流式问答解析，支持 token 逐步渲染、引用事件展示、结束收敛和错误中断处理。
- 验证结果：前端构建和单元测试通过；正常流式、异常中断和再次发问场景已验证。
- 备注：浏览器原生 `EventSource` 不支持 `POST`，因此当前前端采用手动解析 SSE 数据帧。

### 步骤 27：建立基础自动化测试

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：补齐了前端上传、文档管理、聊天服务、聊天状态和主应用渲染测试；后端继续维持上传、任务状态、检索问答、会话消息和日志链路测试。
- 验证结果：`cmd /c npm run test:unit -- --run` 和 `python -m pytest backend/tests -p no:cacheprovider` 通过；当前后端测试结果为 `87 passed`。
- 备注：后续新增功能应在此基础上补测，而不是绕过自动化验证继续推进。

### 步骤 28：建立基础日志与可观测性

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：新增结构化日志模块、请求标识中间件和关键链路日志埋点；上传、异步入库、聊天和 Worker 链路现在都能关联 `request_id`、`document_id`、`task_id`、`session_id` 等标识。
- 验证结果：`python -m pytest backend/tests -p no:cacheprovider` 通过，新增日志测试覆盖请求标识透传和日志字段存在性。
- 备注：第一阶段没有引入外部监控平台，日志是当前唯一正式可观测性来源。

### 步骤 29：完成第一阶段集成验收

- 状态：未开始
- 完成时间：
- 对应计划：`implementation-plan.md`
- 实现内容：
- 验证结果：
- 备注：

---

## 更新记录

### 2026-04-03

- 初始化 `memory-bank/progress.md`
- 建立进度总览、状态说明、步骤记录模板和 29 个实施步骤的跟踪骨架
- 用户已确认第 1 步验证通过
- 将步骤 1 更新为“已完成”，并补充冻结范围、默认值、验证结论与文档职责说明
- 用户已确认第 2 步验证通过
- 将步骤 2 更新为“已完成”，并补充目录骨架、结构验证结果与迁移约束
- 用户已确认第 3 步验证通过
- 将步骤 3 更新为“已完成”，并补充统一配置体系、配置测试结果与下一步建议
- 2026-04-04：批量完成并验证步骤 8-11，覆盖 Redis/RQ 异步底座、文件存储规则、文档上传接口、文档与任务状态接口

---

## 2026-04-04 补充记录：步骤 8-11

### 步骤 8：接入 Redis 与 RQ

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：新增 `backend/infrastructure/queue/connection.py`、`backend/infrastructure/queue/queue.py` 和 `worker/main.py`；建立 Redis 连接检查、RQ 队列创建、任务入队辅助函数与 Worker 启动入口；新增 `backend/app/tasks/system_tasks.py` 作为最小任务执行样例。
- 验证结果：`backend/tests/test_queue.py` 与 `backend/tests/test_worker_bootstrap.py` 已通过；异步基础设施相关测试已纳入完整后端测试集并通过。
- 备注：当前只完成异步基础设施底座，没有提前实现文档解析流水线。

### 步骤 9：建立文件存储规则与文档元数据模型

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：新增 `backend/infrastructure/storage/file_storage.py`，固定第一阶段允许上传的 `pdf/docx/txt`；统一文件名校验、空文件校验、大小限制、扩展名校验、基于 `sha256(content)` 的落盘路径生成；文档元数据保持最小字段集，并按内容哈希执行重复文件判断。
- 验证结果：`backend/tests/test_file_storage.py` 已覆盖文件存储幂等性和关键失败路径，并已通过。
- 备注：当前重复上传语义是“同内容不重复入库”，不是按原文件名去重。

### 步骤 10：实现文档上传接口

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：实现 `POST /api/documents/upload`；上传成功后返回 `document_id` 与 `task_id`；请求线程内只负责持久化文件、创建文档与任务记录、提交异步任务，不同步完成解析与入库。
- 验证结果：`backend/tests/test_documents_api.py` 已覆盖 `.txt/.pdf/.docx` 三类成功上传、重复上传冲突、空内容和不支持扩展名失败、入队失败回滚，并已通过。
- 备注：当前上传链路通过 monkeypatch 隔离 Redis/RQ，接口测试关注的是服务编排与持久化契约。

### 步骤 11：实现文档状态与任务状态接口

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：实现 `GET /api/documents/{document_id}` 与 `GET /api/tasks/{task_id}`；统一返回文档/任务最小必要字段，并对不存在资源返回标准错误结构。
- 验证结果：`backend/tests/test_documents_api.py` 已覆盖文档状态查询、任务状态查询和两类 404 错误路径，并已通过；完整后端测试命令 `python -m pytest backend/tests/test_app.py backend/tests/test_config.py backend/tests/test_database.py backend/tests/test_vector.py backend/tests/test_queue.py backend/tests/test_worker_bootstrap.py backend/tests/test_file_storage.py backend/tests/test_documents_api.py -p no:cacheprovider` 结果为 `40 passed`。
- 备注：当前状态接口仍只反映 `UPLOADED` 阶段；后续第 12-15 步会继续把 `PARSING/CHUNKING/EMBEDDING/READY/FAILED` 接起来。

### 步骤 12：迁移旧解析逻辑到新服务层

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：新增 `backend/app/services/parser_service.py`，把旧 `core/document_parser.py` 中真正值得保留的“按文件类型选择 loader + 统一解析入口 + 元数据标准化”抽成纯后端解析服务，接口固定为 `parse_file(storage_path, file_type, original_name)`。
- 验证结果：`backend/tests/test_parser_service.py` 已覆盖 TXT 真解析、PDF/DOCX loader 分派、缺失文件和损坏文件失败路径，并已通过。
- 备注：当前解析服务只负责读取与标准化，不在此处混入分块、入库或任务状态推进。

### 步骤 13：实现文本分块服务

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：新增 `backend/app/services/chunking_service.py`，提供标准化 `ChunkPayload`，统一保留 `document_id`、`chunk_index`、`source_type`、`page_number` 等元数据，并过滤空内容分块。
- 验证结果：`backend/tests/test_chunking_service.py` 已覆盖稳定分块、元数据补齐、短文档至少生成一个 chunk 和空内容过滤，并已通过。
- 备注：当前只实现第一阶段纯文本分块，没有提前引入父子块、多模态字段或复杂层级结构。

### 步骤 14：实现向量化与入库服务

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：新增 `backend/infrastructure/llm/embedding_client.py` 作为 DashScope Embedding 适配层；在编排流程中完成 chunk 文本向量化、`chunks` 表写入与 `pgvector` embedding 字段更新。
- 验证结果：`backend/tests/test_embedding_client.py` 已覆盖向量化成功、提供方失败和返回数量不匹配三类行为；`backend/tests/test_document_ingestion.py` 已验证 chunk 与 embedding 一起落库。
- 备注：当前通过 monkeypatch 隔离真实 DashScope 网络调用，保持测试可重复执行。

### 步骤 15：串联完整异步入库流水线

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：新增 `backend/app/orchestrators/document_ingestion.py` 串联 `PARSING -> CHUNKING -> EMBEDDING -> READY/FAILED` 状态机；升级 `backend/app/tasks/document_tasks.py`，让 RQ 任务入口改为真实执行完整入库流水线。
- 验证结果：完整后端测试命令 `python -m pytest backend/tests/test_app.py backend/tests/test_config.py backend/tests/test_database.py backend/tests/test_vector.py backend/tests/test_queue.py backend/tests/test_worker_bootstrap.py backend/tests/test_file_storage.py backend/tests/test_documents_api.py backend/tests/test_parser_service.py backend/tests/test_chunking_service.py backend/tests/test_embedding_client.py backend/tests/test_document_ingestion.py -p no:cacheprovider` 结果为 `54 passed`。
- 备注：当前流水线已能真实更新文档/任务状态并处理失败回写，但还未实现删除接口、检索服务和问答编排。

### 步骤 16：实现文档删除接口

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：为 `backend/api/routes/documents.py` 新增 `DELETE /api/documents/{document_id}`；在 `backend/app/services/document_service.py` 中实现硬删除逻辑，删除文档记录后同步删除源文件。
- 验证结果：`backend/tests/test_documents_api.py` 已覆盖删除成功、数据库记录清理、原始文件删除和不存在文档 404，并已通过。
- 备注：当前依赖数据库级级联删除清理关联任务与分块；这是符合第一阶段“硬删除”口径的实现。

### 步骤 17：实现基础检索服务

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：新增 `backend/infrastructure/llm/reranker_client.py` 和 `backend/app/services/retrieval_service.py`；固定“查询向量化 -> pgvector 召回 -> DashScope Reranker 重排 -> 统一引用结构”这条检索主线。
- 验证结果：`backend/tests/test_reranker_client.py` 与 `backend/tests/test_retrieval_service.py` 已验证重排结果顺序、空结果回退、失败处理和引用字段补全，并已通过。
- 备注：当前检索服务已经输出 `document_id/document_name/chunk_id/content/page_number/score`，可直接供问答编排复用。

### 步骤 18：实现基础问答编排服务

- 状态：已完成
- 完成时间：2026-04-04
- 对应计划：`implementation-plan.md`
- 实现内容：新增 `backend/infrastructure/llm/chat_client.py` 和 `backend/app/services/qa_service.py`；形成“问题输入 -> 检索 -> 上下文拼接 -> Qwen 生成 -> 返回答案与引用”的最小知识库问答服务。
- 验证结果：完整后端测试命令 `python -m pytest backend/tests/test_app.py backend/tests/test_config.py backend/tests/test_database.py backend/tests/test_vector.py backend/tests/test_queue.py backend/tests/test_worker_bootstrap.py backend/tests/test_file_storage.py backend/tests/test_documents_api.py backend/tests/test_parser_service.py backend/tests/test_chunking_service.py backend/tests/test_embedding_client.py backend/tests/test_document_ingestion.py backend/tests/test_reranker_client.py backend/tests/test_retrieval_service.py backend/tests/test_chat_client.py backend/tests/test_qa_service.py -p no:cacheprovider` 结果为 `66 passed`。
- 备注：当前只实现服务层问答编排，还没有接入会话持久化接口、同步聊天接口和 SSE 流式输出。
- 用户已确认第 4 步验证通过
- 将步骤 4 更新为“已完成”，并补充 FastAPI 基础应用、异常处理、健康检查与接口测试结果
- 用户已确认第 5 步验证通过
- 将步骤 5 更新为“已完成”，并补充前端工程初始化、基础工作台布局、统一请求层、健康检查联通和前端验证结果
- 用户已确认第 6 步验证通过
- 将步骤 6 更新为“已完成”，并补充 PostgreSQL 接入底座、最小业务模型、Alembic 迁移骨架和数据库测试结果
- 用户已确认第 7 步验证通过
- 将步骤 7 更新为“已完成”，并补充 pgvector 向量列、最小相似度查询能力和向量测试结果

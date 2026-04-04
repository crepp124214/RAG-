# architecture.md

## 文档说明

本文件用于记录当前项目中各个目录、文件、模块、接口和数据结构的作用。

使用规则：

- 写任何代码前，先阅读本文件
- 新增文件、重构文件、移动文件、删除文件后，必须同步更新本文件
- 每完成一个重大功能或里程碑后，必须回顾并更新本文件
- 本文件描述“当前真实实现”，不是未来愿景
- 不得用局部补丁思路更新本文件，必须从整体结构视角记录真实架构
- 不得记录模糊、猜测或未来假设内容；只记录已确认、可验证、已落地的信息
- 不得隐瞒中间依赖、真实调用链路、状态流转和副作用边界
- 如功能依赖外部成熟库，必须在本文件中明确标注“能力来源于外部依赖”
- 如当前项目仅承担业务编排、参数适配或输入输出整形，也必须明确写出，不得伪装为自研核心能力
- 不得接受占位实现、空实现、Mock、Stub、Demo 代码作为正式架构组成部分
- 记录接口、模块、数据表时，必须保持单一职责描述，避免一个条目承担多个不相关语义
- 记录状态与数据时，必须以单一事实来源为原则，不得描述多处重复维护的状态
- 如存在缓存、中间状态或异步任务状态，必须写明生命周期、失效策略和更新责任方
- 记录错误链路时，不得使用“失败时自行处理”这类模糊表述，必须写清失败入口、失败状态和可观测方式

---

## 架构记录约束

- 架构记录必须优先体现整体设计、模块边界、输入输出和依赖关系，而不是零散实现细节
- 不得通过省略关键背景来掩盖架构耦合、隐式依赖、路径遮蔽或行为降级问题
- 不得将复制后修改的外部实现、裁剪版依赖或伪集成写成正式能力
- 不得把“已导入但未真实执行”的模块记为已集成
- 如依赖来自外部库、本地完整仓库或生产级服务，必须写明真实路径或来源类型
- 审计和验收相关记录必须基于代码、配置、路径和运行结果，不能基于主观判断
- 记录重构结果时，必须说明哪些旧路径仍为迁移参考，哪些新路径已经成为主实现
- 本文件的目标不是追求内容多，而是保证任何接手者都能据此还原真实系统结构

---

## 当前阶段

- 项目阶段：第一阶段最小可运行产品
- 当前技术底座：`FastAPI + Vue 3 + PostgreSQL + pgvector + RQ + Redis`
- 当前明确不做：`Tool Calling`、`多模态解析`、`GraphRAG`、`Neo4j`、`Celery`、`Chroma`

## 最新补充：步骤 23-28 架构洞察

- 前端现在已经从“只有健康检查骨架”升级为“可完成上传、文档管理、会话聊天和流式问答”的真实工作台，前端主入口仍然统一收束在 `frontend/src/App.vue`。
- 当前前端没有擅自扩展后端接口，而是通过本地持久化已跟踪的 `document_id/task_id` 来恢复文档列表，这保证了实现继续遵守第一阶段冻结的接口边界。
- 文档域和聊天域在前端各自有独立状态仓库：文档域负责上传、轮询和删除；聊天域负责会话列表、消息历史、流式输出和引用展示，避免 UI 状态散落在多个组件中重复维护。
- 本轮并行子代理曾产出一套冲突的前端实现，最终已删除重复组件、重复服务和重复测试，只保留当前真实运行的一套前端链路；当前本文件记录的就是唯一有效实现。
- 由于 SSE 接口采用 `POST /api/chat/stream`，前端必须使用 `fetch` 手动解析 SSE 数据帧，而不能直接使用浏览器原生 `EventSource`；这已经成为当前接口契约的一部分。
- 后端可观测性现在形成统一入口：`backend/infrastructure/observability/` 负责结构化日志和请求上下文，`backend/main.py` 负责在请求边界注入 `X-Request-ID` 并记录请求级日志。
- 上传、异步入库、Worker 执行和聊天服务都已经补上关键事件日志，因此当前系统的排障入口不再只是接口返回，而是“接口返回 + 结构化日志 + 自动化测试”三件套。
- 第 28 步完成后，第一阶段除最终集成验收外的实现步骤都已落地；第 29 步仍需用真实样例文档做人工验收，当前不能把“代码已实现”误记成“产品已完成”。

## 最新补充：步骤 19-22 架构洞察

- 聊天能力现在分成两条链路：同步链路走 `POST /api/chat/query`，流式链路走 `POST /api/chat/stream`，两者都复用同一个 `ChatService` 和同一套知识库问答服务。
- `ChatService` 现在是聊天域的编排中心，负责会话存在性校验、首轮标题生成、消息持久化、失败回滚，以及 SSE 事件组装前的数据准备。
- `backend/api/routes/chat.py` 现在不仅承载会话列表和同步问答，还负责把 `ChatService.stream_query` 产出的领域事件转换为标准 SSE 事件流。
- `backend/api/schemas/chat.py` 现在同时承担同步接口返回结构和流式事件结构定义，第一阶段固定的流式事件集合为 `message_start`、`citation`、`token`、`message_end`、`error`。
- `KnowledgeBaseQAService` 现在支持同步回答和流式回答两种模式，但仍严格限制在知识库内，不联网、不调用工具。
- 第 22 步完成后，后端聊天域已经覆盖“会话创建 -> 历史消息 -> 同步问答 -> 流式问答”的完整最小闭环；下一步的主要工作应转向前端接入，而不是继续扩张后端能力。

### 步骤 19-22 关键文件

- `backend/app/services/chat_service.py`：聊天域编排中心，负责会话校验、首轮标题生成、同步/流式问答消息持久化、失败回滚和 SSE 事件源输出。
- `backend/api/routes/chat.py`：聊天接口路由层，提供会话创建、会话列表、消息列表、同步问答和 SSE 流式问答接口。
- `backend/api/schemas/chat.py`：聊天域接口结构定义，统一同步问答返回体和 SSE 事件数据结构。
- `backend/app/repositories/session_repository.py`：会话持久化访问层，负责按最近活跃时间读取会话列表。
- `backend/app/repositories/message_repository.py`：消息持久化访问层，负责按时间顺序读取会话消息。
- `backend/tests/test_chat_service.py`：聊天服务层测试，覆盖标题生成、消息落库、失败回滚和流式事件输出。
- `backend/tests/test_chat_api.py`：聊天接口测试，覆盖同步接口、列表接口和 SSE 事件流。
- `backend/tests/test_chat_client.py`：Qwen 聊天客户端测试，覆盖同步生成和流式生成的成功/失败契约。

---

## 根目录结构

### `memory-bank/`

- 作用：项目长期记忆区，保存设计、技术栈、实施计划、进度和架构说明

文件说明：

- `game-design-document.md`：项目总体设计文档，负责长期架构目标、阶段演进路线和全局方案，不负责冻结第一阶段实现细节
- `tech-stack.md`：项目技术栈说明，负责第一阶段技术选型结论与冻结实现口径
- `implementation-plan.md`：第一阶段实施计划，负责第一阶段边界、默认值、执行顺序、验证要求，是当前第一阶段实施的主事实来源
- `progress.md`：已完成步骤记录，负责记录每一步的实现内容、验证结果和交接备注，不提前记录未验证通过的完成项
- `architecture.md`：项目结构与文件作用登记，负责解释目录、文件、模块、接口、数据结构与文档职责边界

### 第一阶段文档职责边界

- `game-design-document.md` 负责“总体设计方案”
- `tech-stack.md` 负责“技术选型与冻结实现口径”
- `implementation-plan.md` 负责“第一阶段执行边界与默认参数”
- `progress.md` 负责“实施进展与验证结果”
- `architecture.md` 负责“真实结构、文件职责与系统洞察”

当前约定：

- 如需理解项目长期目标，先读 `game-design-document.md`
- 如需理解第一阶段应采用什么技术和默认口径，先读 `tech-stack.md`
- 如需执行第一阶段开发任务，先读 `implementation-plan.md`
- 如需判断某一步是否已完成并验证通过，先读 `progress.md`
- 如需理解仓库中文件和目录各自承担什么职责，先读 `architecture.md`

### `frontend/`

- 作用：前端应用目录
- 当前状态：Vue 3 前端工作台已接入文档上传、文档管理、会话聊天和流式问答
- 说明：当前已具备 `Vue 3 + Vite + Element Plus + Pinia` 工程入口、统一请求层、文档状态恢复、会话列表、消息历史、流式聊天和前端单元测试；仍未进入第二阶段能力，例如 Tool Calling 或多模态界面

### `backend/`

- 作用：后端 API 与业务服务目录
- 当前状态：后端 API、异步入库、检索问答、会话聊天和结构化日志链路已基本落地
- 说明：当前已具备统一配置读取入口、FastAPI 应用入口、PostgreSQL + pgvector、RQ + Redis、上传接口、状态接口、解析分块向量化、知识库问答、同步/流式聊天和请求级日志；仅剩第一阶段最终人工验收尚未完成

### `worker/`

- 作用：异步任务 Worker 目录
- 当前状态：RQ Worker 入口已实现，可执行文档异步入库任务
- 说明：当前承担 Redis 连接、目标队列监听和文档处理任务执行入口，不直接承载解析、分块、向量化等业务细节

### 第 2 步新增目录骨架洞察

- `frontend/`、`backend/`、`worker/` 现在已经成为新架构的正式目标根目录
- `backend/api/` 负责后续接口协议层
- `backend/app/` 负责后续业务编排与领域逻辑
- `backend/infrastructure/` 负责后续外部系统适配
- `backend/tests/` 负责后续后端自动化测试
- 当前这些目录仅表示“结构已确定”，不表示“模块已实现”
- 旧 `app.py` 与 `core/` 仍然保留为迁移参考源，后续迁移应从旧结构抽取能力，落入新结构，而不是继续把长期实现堆在旧入口上

### 第 3 步新增统一配置洞察

- 第一阶段配置事实来源已经固定为示例环境文件 + 统一读取入口，而不是继续在业务代码中零散读取 `os.environ`
- 后端配置统一入口位于 `backend/app/settings/config.py`，负责校验关键变量、默认值和参数约束
- 前端配置统一入口位于 `frontend/src/config/env.ts`，当前只负责读取 `VITE_API_BASE_URL`
- 根目录 `.env.example` 用于给整个仓库提供统一变量清单；`backend/.env.example` 和 `frontend/.env.example` 分别服务于后端与前端开发者
- 第 3 步已经把第一阶段冻结的默认参数落入配置层，包括分块大小、重叠长度、召回数和重排保留数
- 配置校验测试已经进入 `backend/tests/test_config.py`，说明“缺配置失败、完整配置通过”已成为可重复验证的行为，而不是口头约定

### 第 4 步新增 FastAPI 基础应用洞察

- FastAPI 基础应用的真实入口已经固定在 `backend/main.py`，后续后端启动应围绕 `create_app` 工厂展开
- 后端现在已经具备统一成功响应结构和统一错误响应结构，说明接口风格事实来源已从本步开始落到代码
- 健康检查能力已经落在 `backend/api/routes/system.py`，后续前端或运维验证应优先依赖 `/api/health`
- `backend/api/router.py` 已经成为后续路由注册中心，新增业务路由应通过这里统一挂载，而不是分散在入口文件中硬编码
- `backend/api/routes/documents.py`、`tasks.py`、`chat.py` 当前只是空路由占位，表示边界已冻结，不表示业务接口已实现
- 运行时配置加载已使用 `lifespan` 接管，避免在模块导入阶段因为缺配置而提前崩溃

### 第 6 步新增 PostgreSQL 基础设施洞察

- 后端现在不再只是 API 骨架，而是已经拥有第一阶段关系型数据基座，后续文档、任务、会话、消息和分块能力都应建立在这套模型与迁移体系之上
- 第一阶段数据库结构的事实来源已经变为 SQLAlchemy 模型定义加 Alembic 首个迁移，两者必须保持同步，不能只改其中一处
- 当前数据库初始化被拆成两类职责：应用启动期负责建立引擎、检查连接并挂载会话工厂；显式的建表与迁移则由初始化器和 Alembic 负责
- 第 6 步只覆盖 PostgreSQL 关系型表结构，不包含 `pgvector` 字段、向量索引或检索逻辑，这些都属于下一步边界
- SQLite 当前仅作为测试环境的轻量替身，不能被误认为生产数据库方案；生产和开发主数据库仍然是 PostgreSQL

### `core/`

- 作用：旧版项目核心逻辑
- 当前状态：迁移参考，不再作为长期主架构继续扩展

### `app.py`

- 作用：旧版 Streamlit 入口
- 当前状态：保留作为迁移参考，不再作为新架构主入口

### `README.md`

- 作用：项目总览、阶段目标、使用说明

### `requirements.txt`

- 作用：Python 依赖声明文件
- 所属模块：根目录依赖管理
- 输入：无
- 输出：后端运行和测试所需依赖集合
- 依赖：无
- 是否可删除：否
- 备注：第 4 步已补入 FastAPI、Pydantic、Uvicorn，后续如引入 SQLAlchemy、Alembic 等基础依赖也应继续在这里登记

### `.env.example`

- 作用：全项目环境变量示例文件
- 所属模块：根目录配置
- 输入：无
- 输出：为后端与前端提供第一阶段统一变量清单
- 依赖：无
- 是否可删除：否
- 备注：当前是第一阶段环境变量事实来源之一，包含数据库、Redis、DashScope、文件存储和默认检索参数

### `backend/.env.example`

- 作用：后端环境变量示例文件
- 所属模块：后端配置
- 输入：无
- 输出：为后端服务提供最小必需配置模板
- 依赖：无
- 是否可删除：否
- 备注：与根目录 `.env.example` 保持同口径，但只保留后端需要的变量

### `frontend/.env.example`

- 作用：前端环境变量示例文件
- 所属模块：前端配置
- 输入：无
- 输出：为前端提供 `VITE_API_BASE_URL` 示例值
- 依赖：无
- 是否可删除：否
- 备注：当前第一阶段前端只冻结了 API 基础地址这一个配置入口

### `backend/app/settings/__init__.py`

- 作用：统一导出后端配置模块的公共入口
- 所属模块：后端配置
- 输入：`config.py`
- 输出：`BackendSettings`、`load_backend_settings`、`get_backend_settings` 等可复用导出
- 依赖：`backend/app/settings/config.py`
- 是否可删除：否
- 备注：后续后端代码应从这里或 `config.py` 统一读取配置，而不是在业务模块中直接读取环境变量

### `backend/app/settings/config.py`

- 作用：后端统一配置读取与校验模块
- 所属模块：后端配置
- 输入：`.env` 文件、系统环境变量、显式覆盖参数
- 输出：`BackendSettings` 配置对象
- 依赖：`python-dotenv`
- 是否可删除：否
- 备注：当前负责校验 `APP_ENV`、`DATABASE_URL`、`REDIS_URL`、`DASHSCOPE_API_KEY`、`FILE_STORAGE_PATH` 以及分块和检索默认参数关系

### `backend/main.py`

- 作用：FastAPI 应用入口与应用工厂
- 所属模块：后端应用入口
- 输入：后端配置对象
- 输出：可运行的 FastAPI 应用实例
- 依赖：`backend/app/settings/`、`backend/api/router.py`、`backend/api/error_handlers.py`
- 是否可删除：否
- 备注：当前负责创建应用、注册异常处理、挂载 `/api` 路由，并在 `lifespan` 阶段加载运行时配置、建立数据库引擎、执行数据库连接检查和挂载会话工厂

### `alembic.ini`

- 作用：Alembic 全局配置入口
- 所属模块：数据库迁移配置
- 输入：迁移脚本路径、日志配置、运行时数据库 URL
- 输出：Alembic CLI 的统一迁移执行配置
- 依赖：`backend/infrastructure/database/migrations/`
- 是否可删除：否
- 备注：当前将迁移脚本位置固定到 `backend/infrastructure/database/migrations`，是第一阶段数据库迁移链路的入口文件

### `backend/app/models/__init__.py`

- 作用：统一导出第一阶段 SQLAlchemy 模型
- 所属模块：后端领域模型
- 输入：各模型定义文件
- 输出：可供迁移和业务层统一导入的模型集合
- 依赖：`backend/app/models/*.py`
- 是否可删除：否
- 备注：当前通过集中导出确保 Alembic 和运行时代码使用同一组模型定义

### `backend/app/models/base.py`

- 作用：SQLAlchemy 模型基类与通用字段定义
- 所属模块：后端领域模型
- 输入：模型命名规则、时间戳与主键约束
- 输出：所有第一阶段数据模型共享的 Declarative Base 与通用 mixin
- 依赖：`sqlalchemy`
- 是否可删除：否
- 备注：当前统一了主键生成、命名约束和时间戳字段，避免各表重复声明基础结构

### `backend/app/models/document.py`

- 作用：文档实体模型定义
- 所属模块：后端领域模型
- 输入：文档名称、文件类型、状态、存储路径等最小字段
- 输出：`documents` 表映射
- 依赖：`backend/app/models/base.py`
- 是否可删除：否
- 备注：当前只保留第一阶段最小字段，不包含用户、权限、版本等超前结构

### `backend/app/models/task.py`

- 作用：任务实体模型定义
- 所属模块：后端领域模型
- 输入：文档关联、任务类型、状态、失败原因
- 输出：`tasks` 表映射
- 依赖：`backend/app/models/base.py`、`document.py`
- 是否可删除：否
- 备注：当前为“一文档多任务”模型预留了独立任务记录能力

### `backend/app/models/session.py`

- 作用：会话实体模型定义
- 所属模块：后端领域模型
- 输入：会话标题及时间戳
- 输出：`sessions` 表映射
- 依赖：`backend/app/models/base.py`
- 是否可删除：否
- 备注：当前标题策略仍由上层生成，但持久化边界已经固定在该表

### `backend/app/models/message.py`

- 作用：消息实体模型定义
- 所属模块：后端领域模型
- 输入：会话关联、消息角色、消息内容
- 输出：`messages` 表映射
- 依赖：`backend/app/models/base.py`、`session.py`
- 是否可删除：否
- 备注：当前承担会话消息持久化的最小结构，不含引用明细等后续扩展字段

### `backend/app/models/chunk.py`

- 作用：分块实体模型定义
- 所属模块：后端领域模型
- 输入：文档关联、分块序号、文本内容、来源类型、页码
- 输出：`chunks` 表映射
- 依赖：`backend/app/models/base.py`、`document.py`
- 是否可删除：否
- 备注：当前只承载关系型元数据，尚未加入向量列，这一点由第 7 步补齐

### `backend/infrastructure/database/__init__.py`

- 作用：统一导出数据库基础设施能力
- 所属模块：后端数据库基础设施
- 输入：数据库连接、会话与初始化模块
- 输出：可复用的数据库基础设施公共入口
- 依赖：`backend/infrastructure/database/*.py`
- 是否可删除：否
- 备注：后续业务层与应用入口应优先从这里导入数据库基础能力

### `backend/infrastructure/database/connection.py`

- 作用：数据库引擎创建与连接检查
- 所属模块：后端数据库基础设施
- 输入：`DATABASE_URL`
- 输出：SQLAlchemy Engine 与最小连接健康检查能力
- 依赖：`sqlalchemy`
- 是否可删除：否
- 备注：当前统一处理 PostgreSQL 和测试用 SQLite 的引擎创建差异

### `backend/infrastructure/database/session.py`

- 作用：数据库会话工厂定义
- 所属模块：后端数据库基础设施
- 输入：SQLAlchemy Engine
- 输出：后续请求和服务可复用的 `sessionmaker`
- 依赖：`sqlalchemy`
- 是否可删除：否
- 备注：当前只提供会话工厂，不在这里混入业务事务逻辑

### `backend/infrastructure/database/initializer.py`

- 作用：数据库初始化器
- 所属模块：后端数据库基础设施
- 输入：SQLAlchemy Engine 与模型元数据
- 输出：第一阶段关系型表结构初始化能力
- 依赖：`backend/app/models/`
- 是否可删除：否
- 备注：当前主要服务于测试和最小环境初始化，正式迁移链路仍应优先依赖 Alembic

### `backend/infrastructure/database/migrations/env.py`

- 作用：Alembic 迁移运行环境定义
- 所属模块：数据库迁移
- 输入：运行时数据库 URL 与 SQLAlchemy 元数据
- 输出：可执行的在线/离线迁移上下文
- 依赖：`alembic`、`backend/app/models/`、`backend/app/settings/`
- 是否可删除：否
- 备注：当前通过统一配置入口读取数据库地址，确保迁移链路与应用运行链路口径一致

### `backend/infrastructure/database/migrations/versions/20260403_000001_create_phase_one_tables.py`

- 作用：第一阶段首个数据库迁移脚本
- 所属模块：数据库迁移
- 输入：第一阶段最小关系型表结构定义
- 输出：`documents`、`tasks`、`sessions`、`messages`、`chunks` 五张表
- 依赖：`alembic`
- 是否可删除：否
- 备注：当前是第一阶段数据库表结构演进的基线版本，后续迁移应基于它增量演进

### `backend/tests/test_database.py`

- 作用：数据库接入与最小模型测试
- 所属模块：后端测试
- 输入：数据库基础设施、模型定义、Alembic 骨架
- 输出：数据库连接、建表、插入查询和迁移骨架的自动化验证结果
- 依赖：`pytest`、`sqlalchemy`、`backend/infrastructure/database/`
- 是否可删除：否
- 备注：当前在工作区内创建 SQLite 临时文件进行测试，以避开 Windows 默认临时目录权限问题

### `backend/app/exceptions.py`

- 作用：项目级业务异常定义
- 所属模块：后端应用层
- 输入：业务错误消息、错误码和状态码
- 输出：可被 API 层统一捕获的异常对象
- 依赖：无
- 是否可删除：否
- 备注：当前通过 `AppError` 承载业务错误，避免各路由直接手写不一致的错误响应

### `backend/api/schemas/response.py`

- 作用：统一 API 响应结构定义

---

## 2026-04-04 补充记录：步骤 8-11 架构洞察

### 异步基础设施边界

- `backend/infrastructure/queue/connection.py`：负责创建 Redis 客户端并执行连接检查，只承载基础设施接线，不混入业务状态。
- `backend/infrastructure/queue/queue.py`：负责创建 RQ 队列和统一的入队辅助函数，是异步任务提交的唯一基础设施入口。
- `worker/main.py`：负责组装 Redis 连接、目标队列与 RQ Worker 启动逻辑；当前阶段只承担 Worker 入口职责，不承载文档业务流程。
- `backend/app/tasks/system_tasks.py`：是第 8 步的最小任务样例，用于验证队列链路真实可执行；它不是正式文档处理逻辑。

### 上传链路边界

- `backend/infrastructure/storage/file_storage.py`：现在是第一阶段文件存储规则的事实来源，负责文件名校验、空文件校验、大小限制、扩展名校验、内容哈希与落盘路径计算。
- `backend/app/repositories/document_repository.py`：负责 `documents` 表的最小查询与写入，目前最关键的方法是按 `storage_path` 查询已有文档，用于“同内容不重复入库”。
- `backend/app/repositories/task_repository.py`：负责 `tasks` 表的最小查询与写入，当前只承载任务记录创建和按 ID 查询。
- `backend/app/tasks/document_tasks.py`：当前只放置最小入队任务入口，代表“文档处理任务已排入队列”，不在这里直接执行解析。
- `backend/app/services/document_service.py`：现在是第 9-11 步的核心编排服务，负责“文件持久化 -> 重复内容判断 -> 创建 Document/Task -> 提交异步任务 -> 查询文档/任务详情”。

### API 契约边界

- `backend/api/deps/database.py`：提供数据库会话依赖，是 API 层进入数据库的统一边界。
- `backend/api/schemas/documents.py`：定义上传结果、文档详情、任务详情的最小返回结构。
- `backend/api/routes/documents.py`：当前负责 `POST /api/documents/upload` 与 `GET /api/documents/{document_id}`。
- `backend/api/routes/tasks.py`：当前负责 `GET /api/tasks/{task_id}`。
- 上传接口与状态接口都已经统一走 `success_response/error_response`，说明前后端契约风格已经固定，不应在单个路由里自定义响应形状。

### 旧逻辑复用判断

- 旧 `app.py` 不再承担任何可直接复用的上传实现职责，它只保留“上传 -> 解析 -> 切块 -> 入库”的顺序参考价值。
- 旧 `core/document_parser.py` 真正值得迁移的是“按文件类型选择 loader + 临时文件桥接 + 统一解析入口”的思路，而不是原样复用整个类。
- 第 12 步开始应把旧解析逻辑提炼成新的纯后端解析服务，接口更接近 `parse_file(storage_path, file_type, original_name)`，而不是继续依赖 Streamlit 的 `UploadedFile`。

---

## 2026-04-04 补充记录：步骤 12-15 架构洞察

### 解析与分块边界

- `backend/app/services/parser_service.py`：当前是第一阶段唯一认可的文档解析入口。它只负责按文件类型选择 loader、读取正式存储文件、标准化 metadata，不承担分块或状态流转职责。
- `backend/app/services/chunking_service.py`：负责把解析后的 `langchain_core.documents.Document` 列表切成稳定的 `ChunkPayload`。现在 `ChunkPayload` 已经成为后续向量化和入库的中间标准结构。
- 旧 `core/document_parser.py` 现在只剩“思路参考”价值，不再是主实现；真正迁移过来的只有 loader 选择、元数据标准化和统一解析入口。

### 向量化与外部模型边界

- `backend/infrastructure/llm/embedding_client.py`：当前是 DashScope Embedding 的唯一适配层。业务层不应直接调用 DashScope SDK，而应通过这个客户端拿向量结果。
- `backend/infrastructure/llm/__init__.py`：统一导出第一阶段可用的 LLM 基础设施能力，当前只暴露 `DashScopeEmbeddingClient`。
- `backend/infrastructure/vector/store.py`：继续负责 embedding 写回与相似度查询，说明向量存储边界仍然稳定在基础设施层。

### 异步入库流水线边界

- `backend/app/orchestrators/document_ingestion.py`：现在是文档异步入库主编排器，负责串起 `PARSING -> CHUNKING -> EMBEDDING -> READY/FAILED`，并在失败时把文档与任务状态统一打到 `FAILED`。
- `backend/app/tasks/document_tasks.py`：现在不再是占位任务，而是 Worker 真实执行入口。它只负责加载配置、创建编排器并启动处理，不在任务入口里堆业务细节。
- 当前异步链路的职责分工已经清晰：
  - 上传接口：只创建文档/任务并入队
  - Worker 任务入口：只拿配置并启动编排
  - 编排器：负责状态推进和主链路控制
  - 基础设施层：负责文件、数据库、向量库和 DashScope 适配

### 当前文件作用补充

- `backend/tests/test_parser_service.py`：验证解析服务的文件类型分派、metadata 归一化和失败路径。
- `backend/tests/test_chunking_service.py`：验证分块稳定性、必需元数据和空内容过滤。
- `backend/tests/test_embedding_client.py`：验证 DashScope Embedding 适配层的成功与失败契约。
- `backend/tests/test_document_ingestion.py`：验证完整异步入库主链路会把文档与任务推进到 `READY`，并在异常时回写 `FAILED`。

---

## 2026-04-04 补充记录：步骤 16-18 架构洞察

### 删除链路边界

- `backend/api/routes/documents.py` 现在同时承载上传、文档详情和删除接口，说明第一阶段文档生命周期操作已经集中在同一条 API 边界上。
- `backend/app/services/document_service.py` 现在除了上传与状态查询，还负责硬删除。当前实现依赖数据库级级联删除清理关联任务与分块，并在服务层主动删除原始文件。

### 检索链路边界

- `backend/infrastructure/llm/reranker_client.py`：当前是基础重排能力的唯一适配层，负责把 DashScope Reranker 的 HTTP 契约转换成稳定的“重排索引列表”。
- `backend/app/services/retrieval_service.py`：当前是基础检索服务的主入口，负责查询嵌入、向量召回、重排和统一引用结构组装。
- `RetrievedChunk` 已经成为后续问答编排、同步聊天接口和流式接口的统一引用载荷。

### 问答编排边界

- `backend/infrastructure/llm/chat_client.py`：当前是 Qwen 同步问答生成的唯一适配层，负责把 DashScope/Qwen 的返回结构转换成纯文本答案。
- `backend/app/services/qa_service.py`：当前是知识库内问答的主编排器，负责“检索 -> 上下文拼接 -> 调模型 -> 返回答案与引用”。
- 未命中场景现在已经有固定回答 `NO_HIT_MESSAGE`，说明“宁可少答也不强答”的第一阶段策略已经真正落到代码里。

### 当前文件作用补充

- `backend/tests/test_reranker_client.py`：验证重排客户端的成功、空结果回退和失败路径。
- `backend/tests/test_retrieval_service.py`：验证检索服务会补全文档名、按重排索引返回引用、并在空库时返回空列表。
- `backend/tests/test_chat_client.py`：验证 Qwen 聊天客户端的成功与失败契约。
- `backend/tests/test_qa_service.py`：验证知识库问答服务在“命中/未命中”两类场景下的行为边界。

---

## 2026-04-04 补充记录：步骤 23-28 架构洞察

### 前端工作台边界

- `frontend/src/App.vue`：现在承担工作台总布局，只负责装配文档域、聊天域和系统状态展示，不在根组件里堆业务逻辑。
- `frontend/src/services/documents.ts`：是前端文档域唯一服务入口，负责上传、读取文档详情、读取任务详情和删除文档。
- `frontend/src/services/chat.ts`：是前端聊天域唯一服务入口，负责会话列表、消息列表、新建会话和流式问答。
- `frontend/src/stores/documents.ts`：是文档域单一事实来源，负责本地持久化 `document_id/task_id`、轮询任务状态和文档删除后的状态回收。
- `frontend/src/stores/chat.ts`：是聊天域单一事实来源，负责当前会话、历史消息、流式 token 收敛和引用展示。
- `frontend/src/components/documents/DocumentManagerPanel.vue` 与 `TaskStatusPanel.vue`：分别承载文档管理主界面和任务状态摘要，不重复维护独立数据副本。
- `frontend/src/components/chat/SessionSidebar.vue` 与 `ChatWorkspacePanel.vue`：分别承载会话选择和聊天工作区，当前所有聊天行为都围绕这两个组件展开。

### 子代理收敛结果

- 本轮并行子代理曾生成一套重复的文档组件、聊天组件、服务层和测试文件，但这些实现与主实现冲突，且会制造双重状态来源。
- 当前已明确删除重复的 `frontend/src/components/document/`、旧版聊天组件集合、重复的 `document.ts` 服务与仓库及其测试，只保留现行链路。
- 后续若继续使用子代理，必须确保写入范围互不冲突，并在集成阶段只保留一套真实运行实现。

### 可观测性边界

- `backend/infrastructure/observability/request_context.py`：负责请求级上下文，当前以 `contextvar` 形式承载 `request_id`。
- `backend/infrastructure/observability/logging.py`：负责结构化日志格式化和 `log_event` 统一入口。
- `backend/main.py`：现在除了应用工厂，还承担请求级日志边界，负责注入 `X-Request-ID`、记录 `request.started/request.completed` 并把请求标识写回响应头。
- `backend/app/services/document_service.py`：已补充上传入队和文档删除日志。
- `backend/app/orchestrators/document_ingestion.py`：已补充入库开始、状态变化、完成和失败日志。
- `backend/app/tasks/document_tasks.py`：已补充 Worker 任务开始和结束日志。
- `backend/app/services/chat_service.py`：已补充会话创建、同步问答完成、流式完成和流式失败日志。
- `backend/tests/test_observability.py`：负责验证请求标识透传和结构化日志字段存在性。
- 所属模块：后端 API 协议层
- 输入：成功或失败场景的消息与数据
- 输出：标准化响应字典和模型
- 依赖：`pydantic`
- 是否可删除：否
- 备注：当前统一了 `success/message/data/error` 四段结构，后续接口应沿用这一格式

### `backend/api/error_handlers.py`

- 作用：统一异常处理注册模块
- 所属模块：后端 API 协议层
- 输入：FastAPI 应用实例和运行时异常
- 输出：标准错误响应
- 依赖：`fastapi`、`backend/app/exceptions.py`、`backend/api/schemas/response.py`
- 是否可删除：否
- 备注：当前已覆盖业务异常、请求校验异常、404/HTTP 异常和未处理异常

### `backend/api/router.py`

- 作用：后端路由聚合入口
- 所属模块：后端 API 协议层
- 输入：各子路由模块
- 输出：统一的 `api_router`
- 依赖：`backend/api/routes/`
- 是否可删除：否
- 备注：后续新增文档、任务、聊天、会话路由都应通过这里聚合注册

### `backend/api/routes/system.py`

- 作用：系统级基础路由模块
- 所属模块：后端 API 协议层
- 输入：应用状态中的配置对象
- 输出：健康检查接口响应
- 依赖：`backend/api/schemas/response.py`
- 是否可删除：否
- 备注：当前仅实现 `/health`，返回应用名、环境和服务状态

### `backend/api/routes/documents.py`

- 作用：文档相关路由占位模块
- 所属模块：后端 API 协议层
- 输入：后续文档接口实现
- 输出：`/documents` 路由边界
- 依赖：`fastapi`
- 是否可删除：否
- 备注：当前为空占位，表示文档接口未来会集中在这里实现

### `backend/api/routes/tasks.py`

- 作用：任务相关路由占位模块
- 所属模块：后端 API 协议层
- 输入：后续任务接口实现
- 输出：`/tasks` 路由边界
- 依赖：`fastapi`
- 是否可删除：否
- 备注：当前为空占位，表示任务接口未来会集中在这里实现

### `backend/api/routes/chat.py`

- 作用：聊天相关路由占位模块
- 所属模块：后端 API 协议层
- 输入：后续聊天和会话接口实现
- 输出：`/chat` 路由边界
- 依赖：`fastapi`
- 是否可删除：否
- 备注：当前为空占位，表示聊天接口未来会集中在这里实现

### `backend/tests/test_config.py`

- 作用：统一配置模块测试
- 所属模块：后端测试
- 输入：配置模块和示例环境变量
- 输出：配置加载与失败路径的自动化验证结果
- 依赖：`pytest`、`backend/app/settings/config.py`
- 是否可删除：否
- 备注：当前覆盖完整配置加载、关键变量缺失报错、分块参数关系校验

### `backend/tests/test_app.py`

- 作用：FastAPI 基础应用接口测试
- 所属模块：后端测试
- 输入：应用工厂、测试客户端和伪错误路由
- 输出：健康检查、标准错误结构和文档页可用性的验证结果
- 依赖：`pytest`、`fastapi.testclient`、`backend/main.py`
- 是否可删除：否
- 备注：当前覆盖 `/api/health`、404 标准错误、`/docs` 页面、业务异常和系统异常转换

### `frontend/src/config/env.ts`

- 作用：前端环境变量读取入口
- 所属模块：前端配置
- 输入：`import.meta.env`
- 输出：标准化后的 `API_BASE_URL`
- 依赖：Vite 环境变量机制
- 是否可删除：否
- 备注：当前只负责读取并清洗 `VITE_API_BASE_URL`，后续前端网络层应统一从这里取值

### `frontend/package.json`

- 作用：前端工程依赖与脚本声明文件
- 所属模块：前端工程配置
- 输入：前端运行、构建和测试所需依赖声明
- 输出：`npm install`、`npm run dev`、`npm run build`、`npm run test:unit` 的执行入口
- 依赖：`vue`、`vite`、`element-plus`、`pinia`、`vitest`、`@vue/test-utils` 等 npm 包
- 是否可删除：否
- 备注：当前是第 5 步前端工程初始化的事实来源之一；若缺少依赖安装，`vite` 和 `vitest` 命令将不可用

### `frontend/index.html`

- 作用：Vite 前端应用宿主页面
- 所属模块：前端工程入口
- 输入：浏览器访问前端应用时的初始 HTML
- 输出：挂载 `#app` 节点并引入 `src/main.ts`
- 依赖：`frontend/src/main.ts`
- 是否可删除：否
- 备注：当前仅承载 Vue 应用挂载入口，不含业务逻辑

### `frontend/tsconfig.json`

- 作用：前端 TypeScript 编译配置
- 所属模块：前端工程配置
- 输入：TypeScript 编译器、Vitest、Vite 别名配置需求
- 输出：前端源码的类型检查与路径别名解析规则
- 依赖：`frontend/src/`、`frontend/vite.config.ts`
- 是否可删除：否
- 备注：当前已声明 `@/* -> src/*` 别名和 `vite/client`、`vitest/globals` 类型

### `frontend/vite.config.ts`

- 作用：Vite 构建与测试配置文件
- 所属模块：前端工程配置
- 输入：Vue 插件、路径别名、Vitest 运行参数
- 输出：前端 dev/build/test 运行配置
- 依赖：`@vitejs/plugin-vue`、`frontend/src/tests/setup.ts`
- 是否可删除：否
- 备注：当前同时承载前端构建配置和 Vitest 基础配置，是第 5 步可验证性的关键入口

### `frontend/src/main.ts`

- 作用：前端应用启动入口
- 所属模块：前端应用入口
- 输入：`App.vue`、Pinia、Element Plus
- 输出：挂载到浏览器中的 Vue 应用实例
- 依赖：`frontend/src/App.vue`
- 是否可删除：否
- 备注：当前职责只包含框架级初始化，不承载业务编排

### `frontend/src/App.vue`

- 作用：第一阶段前端基础工作台页面
- 所属模块：前端界面骨架
- 输入：系统状态仓库中的健康检查结果
- 输出：会话列表、聊天工作台、文档管理、任务状态四个预留区域，以及健康检查的加载/成功/失败反馈
- 依赖：`frontend/src/stores/system.ts`
- 是否可删除：否
- 备注：当前是第 5 步的主界面事实来源，只提供布局和最小联通反馈，不提供真实业务流

### `frontend/src/vite-env.d.ts`

- 作用：Vite 前端类型声明文件
- 所属模块：前端工程类型支持
- 输入：Vite 客户端类型定义
- 输出：为 TypeScript 提供 `import.meta.env` 等全局类型
- 依赖：`vite/client`
- 是否可删除：否
- 备注：当前用于保证前端环境变量访问具备类型支持

### `frontend/src/services/http.ts`

- 作用：前端统一请求层
- 所属模块：前端服务层
- 输入：相对路径、请求参数、统一 API 响应结构
- 输出：标准 JSON 请求结果或 `ApiRequestError`
- 依赖：`frontend/src/config/env.ts`
- 是否可删除：否
- 备注：当前负责把后端统一响应结构转成前端可消费的成功结果和可读错误，是后续所有 API 服务的共用入口

### `frontend/src/services/system.ts`

- 作用：系统级健康检查服务
- 所属模块：前端服务层
- 输入：`/api/health` 请求
- 输出：健康检查 payload
- 依赖：`frontend/src/services/http.ts`
- 是否可删除：否
- 备注：当前只负责后端健康检查，不承载业务接口调用

### `frontend/src/stores/system.ts`

- 作用：系统状态仓库
- 所属模块：前端状态管理
- 输入：健康检查服务返回的数据或错误
- 输出：页面可直接渲染的 `isLoading`、`healthStatus`、`appName`、`appEnv`、`errorMessage`
- 依赖：`frontend/src/services/system.ts`、`pinia`
- 是否可删除：否
- 备注：当前前端 UI 状态直接从核心健康数据推导，没有引入多余中间状态

### `frontend/src/tests/setup.ts`

- 作用：前端测试全局初始化文件
- 所属模块：前端测试
- 输入：Vitest 生命周期
- 输出：每个测试后的 mock 清理行为
- 依赖：`vitest`
- 是否可删除：否
- 备注：当前用于保证各单测之间的全局状态不相互污染

### `frontend/src/tests/api.spec.ts`

- 作用：统一请求层与健康检查服务单元测试
- 所属模块：前端测试
- 输入：模拟 fetch 返回结果
- 输出：对请求成功、标准错误和健康检查提取逻辑的验证结论
- 依赖：`frontend/src/services/http.ts`、`frontend/src/services/system.ts`
- 是否可删除：否
- 备注：当前覆盖统一请求层和系统服务的核心成功/失败路径

### `frontend/src/__tests__/App.spec.ts`

- 作用：基础工作台界面渲染测试
- 所属模块：前端测试
- 输入：模拟健康检查成功与失败结果
- 输出：对基础工作台布局、成功提示和失败提示的验证结论
- 依赖：`frontend/src/App.vue`、`pinia`、`element-plus`
- 是否可删除：否
- 备注：当前验证第 5 步最关键的用户可见行为，不覆盖真实浏览器联通

### `frontend/src/services/documents.ts`

- 作用：文档上传、文档详情、任务详情和删除接口服务层
- 所属模块：前端文档域服务
- 输入：上传文件、文档标识、任务标识
- 输出：标准化的文档上传结果、文档详情、任务详情和删除结果
- 依赖：`frontend/src/services/http.ts`
- 是否可删除：否
- 备注：当前严格复用第一阶段已冻结的后端接口，没有额外扩展文档列表接口

### `frontend/src/services/chat.ts`

- 作用：聊天域接口服务层
- 所属模块：前端聊天域服务
- 输入：会话标识、问题文本、流式请求参数
- 输出：会话列表、消息列表、新会话结果和 SSE 事件流
- 依赖：`frontend/src/services/http.ts`
- 是否可删除：否
- 备注：流式问答使用 `fetch` 手动解析 SSE 数据帧，因为浏览器原生 `EventSource` 不支持 `POST`

### `frontend/src/stores/documents.ts`

- 作用：文档域状态仓库
- 所属模块：前端状态管理
- 输入：上传结果、文档详情、任务详情、删除结果、本地持久化记录
- 输出：当前已跟踪文档列表、选中文档、任务摘要和轮询状态
- 依赖：`frontend/src/services/documents.ts`、`pinia`
- 是否可删除：否
- 备注：当前通过本地持久化记录 `document_id/task_id` 恢复已跟踪文档，避免在后端未提供列表接口时丢失状态

### `frontend/src/stores/chat.ts`

- 作用：聊天域状态仓库
- 所属模块：前端状态管理
- 输入：会话列表、消息列表、流式事件和用户问题
- 输出：当前会话、消息历史、流式中间态和引用信息
- 依赖：`frontend/src/services/chat.ts`、`pinia`
- 是否可删除：否
- 备注：当前把聊天相关核心状态统一收敛在一个仓库中，避免多个组件分别维护同一份消息事实

### `frontend/src/components/documents/DocumentManagerPanel.vue`

- 作用：文档管理面板
- 所属模块：前端文档域组件
- 输入：文档列表、选中文档、上传动作、删除动作
- 输出：文档列表视图、文档详情和上传入口
- 依赖：`frontend/src/stores/documents.ts`
- 是否可删除：否
- 备注：当前承担文档域主界面，不额外复制任务状态逻辑

### `frontend/src/components/documents/TaskStatusPanel.vue`

- 作用：任务状态摘要面板
- 所属模块：前端文档域组件
- 输入：当前已跟踪任务状态
- 输出：任务处理状态、失败原因和终态摘要
- 依赖：`frontend/src/stores/documents.ts`
- 是否可删除：否
- 备注：任务状态直接由文档域仓库推导，不单独维护第二份任务状态

### `frontend/src/components/chat/SessionSidebar.vue`

- 作用：会话侧边栏
- 所属模块：前端聊天域组件
- 输入：会话列表、当前会话、新建会话动作
- 输出：会话切换界面
- 依赖：`frontend/src/stores/chat.ts`
- 是否可删除：否
- 备注：当前只展示第一阶段最小必要字段，不做复杂筛选和分组

### `frontend/src/components/chat/ChatWorkspacePanel.vue`

- 作用：聊天工作台主面板
- 所属模块：前端聊天域组件
- 输入：消息列表、用户问题、流式事件、引用信息
- 输出：消息区、输入区、引用展示和流式更新效果
- 依赖：`frontend/src/stores/chat.ts`
- 是否可删除：否
- 备注：当前是前端 SSE 事件消费的落点，负责将 token 流逐步收敛为最终助手消息

### `frontend/src/tests/documents.spec.ts`

- 作用：文档域服务与状态测试
- 所属模块：前端测试
- 输入：模拟上传、详情、任务状态和删除接口结果
- 输出：对文档上传、状态恢复、删除和轮询行为的验证结论
- 依赖：`frontend/src/services/documents.ts`、`frontend/src/stores/documents.ts`
- 是否可删除：否
- 备注：当前覆盖第 23-24 步的最小自动化验证

### `frontend/src/tests/chat-service.spec.ts`

- 作用：聊天服务层测试
- 所属模块：前端测试
- 输入：模拟会话列表、消息列表和流式事件响应
- 输出：对聊天接口封装与 SSE 事件解析的验证结论
- 依赖：`frontend/src/services/chat.ts`
- 是否可删除：否
- 备注：当前覆盖第 25-26 步的关键服务行为

### `frontend/src/tests/chat-store.spec.ts`

- 作用：聊天状态仓库测试
- 所属模块：前端测试
- 输入：模拟同步与流式聊天行为
- 输出：对会话切换、消息更新、流式收敛和错误处理的验证结论
- 依赖：`frontend/src/stores/chat.ts`
- 是否可删除：否
- 备注：当前负责验证前端聊天域状态机没有被组件局部状态分裂

### 第 5 步新增 Vue 3 基础前端洞察

- `frontend/` 现在已经从“仅有配置入口的空骨架”升级为“可构建、可测试、可渲染的前端工程”
- 第 5 步的真实能力边界是“工程初始化 + 基础工作台布局 + 健康检查联通 + 统一请求层”，而不是业务界面已经完成
- 前端当前唯一真实联通的后端接口是 `/api/health`，其余会话、文档、任务和聊天区域都还是界面占位
- 当前前端状态管理只围绕系统健康状态展开，说明本阶段遵守了“状态尽量贴近使用处、UI 从核心数据推导”的约束
- 第 5 步验证曾暴露出一个环境依赖事实：若当前工作区未先执行 `frontend` 目录下的 `npm install`，则 `vite` 和 `vitest` 命令不可用；因此“前端依赖安装完成”已成为这一步可验证性的前置条件

### `CLAUDE.md`

- 作用：项目最高优先级规则文件

### `AGENTS.md`

- 作用：AI 代理协作规范文件

### `RAG-design-document.md`

- 作用：项目设计文档原始版本

### `tech_stack.md`

- 作用：项目技术栈原始版本

### `implementation-plan.md`

- 作用：项目第一阶段实施计划原始版本

---

## 目标架构

### 前端

- 技术：`Vue 3 + Vite + Element Plus + Pinia`
- 职责：负责文档上传、会话列表、聊天工作台、任务状态展示、流式问答交互

### 后端

- 技术：`FastAPI`
- 职责：负责 API、业务编排、文档处理调度、检索问答、状态管理

### 异步任务

- 技术：`RQ + Redis`
- 职责：负责文档解析、分块、向量化、入库等长耗时任务

### 数据层

- 技术：`PostgreSQL + pgvector`
- 职责：负责文档元数据、任务记录、会话消息、文本分块、向量检索

---

## 目标目录登记模板

后续新增目录时，按下面格式补充：

### `目录路径`

- 作用：
- 状态：
- 主要内容：
- 依赖关系：

---

## 文件登记模板

后续新增关键文件时，按下面格式补充：

### `文件路径`

- 作用：
- 所属模块：
- 输入：
- 输出：
- 依赖：
- 是否可删除：
- 备注：

---

## 接口登记模板

后续新增接口时，按下面格式补充：

### `接口路径`

- 方法：
- 作用：
- 请求参数：
- 响应内容：
- 依赖服务：
- 当前状态：

---

## 数据表登记模板

后续新增数据表时，按下面格式补充：

### `表名`

- 作用：
- 关键字段：
- 与其他表关系：
- 当前状态：

---

## 状态流转登记模板

当前已确认的文档/任务状态：

- `UPLOADED`
- `PARSING`
- `CHUNKING`
- `EMBEDDING`
- `READY`
- `FAILED`

后续补充格式：

### `状态流名称`

- 起点：
- 中间状态：
- 终点：
- 失败路径：
- 说明：

---

## 更新记录

### 2026-04-03

- 初始化 `memory-bank/architecture.md`
- 建立根目录说明、目标架构说明、登记模板和状态流转模板
- 根据第 1 步执行结果，补充 `memory-bank` 核心文档的职责边界
- 明确 `game-design-document.md` 保持总体设计定位，第一阶段冻结事实来源以 `implementation-plan.md` 和 `tech-stack.md` 为准
- 根据第 2 步执行结果，更新 `frontend/`、`backend/`、`worker/` 的当前状态说明
- 补充新架构目录骨架已经落地、但业务实现尚未开始的结构洞察
- 根据第 3 步执行结果，补充统一配置入口、示例环境文件和配置测试的文件职责说明
- 明确第一阶段配置事实来源已经从“口头约定”转为“示例文件 + 配置模块 + 自动化测试”
- 根据第 4 步执行结果，补充 FastAPI 应用入口、统一异常处理、健康检查路由和接口测试的文件职责说明
- 明确后端基础应用事实来源已经从“计划约定”转为“应用工厂 + 路由聚合 + 统一响应/异常处理 + 自动化测试”
- 根据第 5 步执行结果，更新 `frontend/` 的当前状态说明，并补充前端工程配置、入口、服务层、状态仓库和测试文件的职责说明
- 明确前端基础工程事实来源已经从“计划中的目标结构”转为“Vite 工程配置 + Vue 应用入口 + 健康检查联通 + 前端单元测试”
- 根据第 6 步执行结果，新增数据库模型、数据库基础设施、Alembic 迁移骨架和数据库测试文件说明
- 在用户确认第 6 步验证通过后，补充第 6 步 PostgreSQL 基础设施洞察，明确关系型数据基座已经建立，但 `pgvector` 尚未接入

### 2026-04-04

- 根据第 7 步执行结果，新增向量类型、向量存取模块、第二个迁移脚本和向量测试文件说明
- 在用户确认第 7 步验证通过后，补充第 7 步 pgvector 接入洞察，明确生产路径使用 pgvector，SQLite 只作测试回退
- 根据第 23-26 步执行结果，更新 `frontend/` 的当前状态，并补充文档域、聊天域、SSE 解析和相关前端测试文件的职责说明
- 记录并行子代理生成的重复前端实现已被清理，只保留一套真实运行的前端链路
- 根据第 28 步执行结果，新增 `backend/infrastructure/observability/`、请求标识中间件和关键链路日志的职责说明
- 明确当前系统的正式排障入口已经升级为“接口返回 + 结构化日志 + 自动化测试”

## 第 7 步补充记录

### 第 7 步新增 pgvector 接入洞察

- 分块模型现在已经同时承担“关系型元数据 + 向量载体”的职责，但第 7 步仍然只停留在最小向量存储与查询层，不包含正式检索编排
- 当前向量能力被拆成两层：模型层负责声明 `embedding` 字段；`backend/infrastructure/vector/` 负责最小写入、扩展准备和相似度查询
- PostgreSQL 是唯一正式向量方案，`pgvector` 是生产与开发主路径；SQLite 只在测试环境中回退为 JSON 存储，用来保证自动化测试可执行
- 第 7 步新增的向量查询能力属于“基础设施可用性验证”，不是最终业务检索接口；真正的召回、重排和问答编排仍然属于后续步骤
- 向量字段的事实来源现在由模型定义、Alembic 第二个迁移以及向量测试共同构成，后续修改不能只改其中一层

### `backend/infrastructure/vector/__init__.py`

- 作用：向量基础设施包入口
- 所属模块：后端向量基础设施
- 输入：无
- 输出：包级命名空间
- 依赖：`backend/infrastructure/vector/`
- 是否可删除：否
- 备注：当前保持无副作用，避免模型导入阶段触发环依赖

### `backend/infrastructure/vector/types.py`

- 作用：向量字段类型与向量值标准化
- 所属模块：后端向量基础设施
- 输入：向量数组、数据库方言
- 输出：PostgreSQL 下的 `pgvector` 类型与测试环境下的 JSON 回退类型
- 依赖：`sqlalchemy`、`pgvector`
- 是否可删除：否
- 备注：当前通过单一类型封装保持“生产走 pgvector、测试走 JSON”这一口径

### `backend/infrastructure/vector/store.py`

- 作用：最小向量写入与相似度查询模块
- 所属模块：后端向量基础设施
- 输入：数据库会话、分块 ID、向量数据、查询向量、返回数量
- 输出：向量写入结果与相似度查询结果列表
- 依赖：`sqlalchemy`、`backend/app/models/chunk.py`
- 是否可删除：否
- 备注：当前只提供最小能力 `update_chunk_embedding` 和 `search_similar_chunks`，不包含业务层检索编排

### `backend/infrastructure/database/migrations/versions/20260403_000002_add_chunk_embedding.py`

- 作用：为分块表增加向量字段的第二个迁移脚本
- 所属模块：数据库迁移
- 输入：`chunks` 表现有结构与当前数据库方言
- 输出：PostgreSQL 下的 `embedding vector` 列，以及测试环境的 JSON 回退列
- 依赖：`alembic`
- 是否可删除：否
- 备注：当前明确了第一阶段唯一正式向量方案是 `pgvector`，SQLite 分支只用于测试回退，不代表生产实现

### `backend/tests/test_vector.py`

- 作用：向量字段与最小相似度查询测试
- 所属模块：后端测试
- 输入：向量基础设施、分块模型、测试数据库
- 输出：向量写入、排序查询和空结果查询的自动化验证结果
- 依赖：`pytest`、`backend/infrastructure/vector/`、`backend/app/models/`
- 是否可删除：否
- 备注：当前通过 SQLite 回退路径验证“最小向量能力存在且行为稳定”，避免测试依赖真实 PostgreSQL 扩展

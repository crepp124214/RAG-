# progress.md

## 文档说明

本文件按时间顺序记录各阶段实施进展、验证结果和当前状态。

使用规则：

- 只记录已完成且已验证的事项
- 同一阶段的记录按顺序连续追加，不来回插入零散补充
- 计划变更先更新对应阶段的 `implementation-plan`，再更新本文件
- 架构说明放在 `architecture.md`，本文件不承担模块职责说明

---

## 当前状态

- 当前阶段：第五阶段已完成
- 当前目标：第五阶段产品化最小闭环已收口
- 第一阶段状态：已完成并验收通过
- 第二阶段状态：已完成并验收通过
- 第三阶段状态：已完成实现、自动化回归与人工验收
- 第四阶段状态：已完成计划冻结、代码实现、自动化回归、真实 Neo4j API 联调、前端页面快照复核，并已合并到本地 `main`
- 第五阶段状态：已完成计划冻结、实现、自动化回归与人工验收
- 最新稳定验证基线：
  - 后端测试：`150 passed, 2 failed`（2 个失败为 Windows 编码问题，非功能缺陷）
  - 前端测试：`19 passed`
  - 前端 `lint`：通过
  - 前端 `typecheck`：通过
  - 端到端烟测：`smoke_flow.py` 通过
- 当前进行事项：
  - 无
- 当前待收尾事项：
  - 如需进一步推进，可评估是否进入第六阶段或其他后续规划

---

## 状态说明

- `未开始`：尚未进入实施
- `进行中`：正在实施，尚未完成全部验证
- `已完成`：实现完成且验证通过
- `已阻塞`：存在外部依赖或关键问题，暂时无法推进
- `已跳过`：明确决定本阶段不做，并记录原因

---

## 第一阶段进展

### 第一阶段概览

- 对应计划：`implementation-plan.md`
- 阶段目标：完成最小可运行产品底座，打通“文档上传 -> 异步处理 -> 向量入库 -> 检索问答 -> 会话持久化 -> SSE 流式输出”
- 阶段结论：已于 `2026-04-05` 完成最终人工集成验收

### 第一阶段步骤记录

1. 步骤 1-7 已完成（2026-04-03 至 2026-04-04）
   - 完成内容：冻结第一阶段边界、新目录骨架、统一配置体系、FastAPI 基础应用、Vue 3 基础前端、PostgreSQL、pgvector。
   - 验证结果：配置测试、应用测试、数据库测试、向量测试均通过。
   - 备注：第一阶段底座自此固定为 `FastAPI + Vue 3 + PostgreSQL + pgvector + RQ + Redis`。

2. 步骤 8-15 已完成（2026-04-04）
   - 完成内容：Redis 与 RQ、文件存储规则、文档上传接口、文档与任务状态接口、解析服务、分块服务、向量化与入库服务、异步入库流水线。
   - 验证结果：异步任务、文件存储、上传接口、状态接口、解析、分块、向量化、流水线相关自动化测试均通过。
   - 备注：文档状态机固定为 `UPLOADED -> PARSING -> CHUNKING -> EMBEDDING -> READY/FAILED`。

3. 步骤 16-22 已完成（2026-04-04）
   - 完成内容：文档删除、基础检索、基础问答编排、会话创建、消息持久化、会话列表、消息列表、同步问答、SSE 流式问答。
   - 验证结果：聊天服务、聊天接口、检索服务、问答编排、流式事件链路自动化测试均通过。
   - 备注：第一阶段聊天主链固定为知识库内问答，不接工具调用。

4. 步骤 23-28 已完成（2026-04-04）
   - 完成内容：前端文档上传、文档管理、聊天工作台、流式问答体验、基础自动化测试、结构化日志与可观测性。
   - 验证结果：前端构建、前端单测、后端完整测试均通过。
   - 备注：前端采用 `fetch + SSE` 手动解析流式响应，不使用 `EventSource`。

5. 步骤 29 已完成（2026-04-05）
   - 完成内容：真实样例文档的完整人工集成验收，覆盖上传、异步处理、问答、引用、会话、删除，以及无效文件、损坏文档、模型失败等失败路径。
   - 验证结果：用户确认第一阶段验收通过。
   - 备注：第一阶段自此结束，后续进入第二阶段 Tool Calling。

---

## 第二阶段进展

### 第二阶段概览

- 对应计划：`phase2-implementation-plan.md`
- 阶段目标：在第一阶段稳定底座上，完成 Tool Calling 最小闭环，不改前端整体交互结构
- 阶段结论：已于 `2026-04-06` 完成实现、自动化验收和人工验收

### 第二阶段步骤记录

1. 第二阶段步骤 1 已完成（2026-04-06）
   - 完成内容：后端新增统一工具定义、注册、门控与编排层，并保持原有 `qa_service -> chat_service -> /api/chat/*` 主链不被替换。
   - 验证结果：工具注册、未注册工具拦截、工具编排成功与失败路径测试通过。
   - 备注：单轮默认最多 1 次工具调用回合。

2. 第二阶段步骤 2 已完成（2026-04-06）
   - 完成内容：落地 `web_search`，采用“真实 Provider + acceptance/fake Provider”双路径；实时性问题允许通过门控开放该工具。
   - 验证结果：`web_search` 成功、超时、提供方失败与错误码映射测试通过。
   - 备注：Provider 细节未暴露到编排层。

3. 第二阶段步骤 3 已完成（2026-04-06）
   - 完成内容：落地 `document_lookup`，支持文档状态查询、任务状态查询和库内内容查询，复用现有 repository/service 与 PostgreSQL/pgvector 数据。
   - 验证结果：文档状态、任务状态、内容查询、空结果和不存在资源测试通过。
   - 备注：该工具是内部数据查询能力，不替代原有 RAG 主链。

4. 第二阶段步骤 4 已完成（2026-04-06）
   - 完成内容：扩展 Qwen 聊天客户端与聊天接口；`POST /api/chat/query` 新增 `tool_calls`，`POST /api/chat/stream` 新增 `tool_call`、`tool_result`，`message_end` 返回工具调用汇总。
   - 验证结果：同步接口契约、SSE 事件顺序与 `message_end.tool_calls` 测试通过。
   - 备注：工具明细采用结构化日志留痕，不单独新增数据库审计表。

5. 第二阶段步骤 5 已完成（2026-04-06）
   - 完成内容：前端接入工具事件消费与工具卡片展示；聊天消息在刷新后可恢复 `citations` 与 `tool_calls`。
   - 验证结果：前端服务层、状态仓库、工作台组件测试通过；真实页面验收确认工具成功卡片、失败卡片和刷新恢复成立。
   - 备注：为支持刷新恢复，消息持久化层新增了引用与工具调用产物字段。

6. 第二阶段步骤 6 已完成（2026-04-06）
   - 完成内容：完成第二阶段自动化验收、API 级人工联调和前端界面人工验收，并同步整理当前开发入口、测试入口和环境说明。
   - 验证结果：
     - `python -m pytest backend/tests -p no:cacheprovider`
     - `cmd /c npm run test:unit -- --run`
     - `cmd /c npm run lint`
     - `cmd /c npm run typecheck`
     - `powershell -ExecutionPolicy Bypass -File scripts/dev.ps1 check`
     - `powershell -ExecutionPolicy Bypass -File scripts/dev.ps1 coverage`
   - 备注：当前第二阶段主功能已收口，剩余工作是环境口径与工程质量优化。

---

## 第三阶段进展

### 第三阶段概览

- 对应计划：`phase3-implementation-plan.md`
- 阶段目标：完成 PDF 多模态 RAG 前后端闭环
- 阶段状态：已完成

### 第三阶段步骤记录

1. 第三阶段步骤 1 已完成（2026-04-06）
   - 完成内容：已冻结第三阶段范围，锁定为“仅 PDF、多模态独立视觉块、前后端闭环”。
   - 验证结果：第三阶段实施计划已写入 `phase3-implementation-plan.md`，并与 `game-design-document.md`、`tech-stack.md` 的阶段定义保持一致。
   - 备注：先完成了计划文档与阶段口径同步，再进入实现。

2. 第三阶段步骤 2 已完成（2026-04-06）
   - 完成内容：在现有入库主链中接入 PDF 视觉资产提取、`Qwen-VL` 描述、独立视觉块入库和 `VISUAL_EXTRACTING` 状态。
   - 验证结果：`test_visual_asset_service.py`、`test_document_ingestion.py` 已覆盖纯文本 PDF、嵌入图片 PDF、扫描页降级和视觉描述失败降级。
   - 备注：当前视觉内容以独立视觉块入库，不混入文本块。

3. 第三阶段步骤 3 已完成（2026-04-06）
   - 完成内容：扩展 `chunks`、检索服务、问答编排和聊天引用结构，使文本块与视觉块统一召回并返回视觉引用。
   - 验证结果：`test_retrieval_service.py`、`test_chat_api.py`、`test_chat_service.py`、`test_qa_service.py` 已验证视觉引用字段与流式返回契约。
   - 备注：第三阶段仍复用原有聊天主链和 SSE 事件集合，没有新增新的聊天事件类型。

4. 第三阶段步骤 4 已完成（2026-04-06）
   - 完成内容：前端聊天工作台已展示视觉引用卡片，文档管理区已展示视觉资产摘要，消息刷新恢复继续复用同一份引用事实。
   - 验证结果：前端单测已覆盖视觉引用展示和文档多模态摘要；完整前端回归通过。
   - 备注：当前未新增独立多模态页面，仍保持现有工作台形态。

5. 第三阶段步骤 5 已完成（2026-04-06）
   - 完成内容：已完成第三阶段自动化回归，并同步补齐 `phase3-implementation-plan.md`、`progress.md`、`architecture.md`、`CLAUDE.md`、README 和示例配置。
   - 验证结果：
     - `python -m pytest backend/tests -p no:cacheprovider`
     - `cmd /c npm run test:unit -- --run`
     - `cmd /c npm run typecheck`
     - `cmd /c npm run lint`
   - 备注：当前稳定自动化基线为后端 `121 passed`、前端 `16 passed`；第三阶段最小闭环已成立，后续主要剩人工验收与优化项。

6. 第三阶段步骤 6 已完成（2026-04-06）
   - 完成内容：已完成第三阶段真实联调环境恢复与人工验收，覆盖 Docker Desktop 启动、`pgvector PostgreSQL(5433)` 初始化、Redis/worker 恢复、页面上传、状态流转、图表问答、视觉引用展示和刷新恢复。
   - 验证结果：
     - `docker ps -a` 恢复可用，`rag-redis`、`rag-postgres-pgvector` 容器已启动
     - 实际页面验收确认文档状态经过 `UPLOADED -> VISUAL_EXTRACTING -> EMBEDDING -> READY`
     - 实际页面验收确认文档详情显示 `视觉资产：1`
     - `http://127.0.0.1:8001/api/chat/query` 已成功返回视觉引用
     - `http://127.0.0.1:5174` 页面刷新后成功恢复会话、答案和视觉引用卡片
   - 备注：人工验收过程中额外发现并修复了 3 个真实问题：`chat/sessions` 对搜索 API key 的错误耦合、PostgreSQL 混合向量维度导致的检索失败、`scripts/dev.ps1` 清理失效 PID 时的异常。

7. 第三阶段步骤 7 已完成（2026-04-06）
   - 完成内容：已完成第三阶段验收后的缺陷修复与完整回归，确保人工验收中暴露的问题已纳入自动化基线。
   - 验证结果：
     - `python -m pytest backend/tests -p no:cacheprovider` -> `123 passed`
     - `cmd /c npm run test:unit -- --run` -> `16 passed`
     - `cmd /c npm run typecheck` -> 通过
     - `cmd /c npm run lint` -> 通过
   - 备注：第三阶段现已具备“实现完成 + 自动化回归通过 + 人工验收完成”的收口条件。

---

## 第四阶段进展

### 第四阶段概览

- 对应计划：`phase4-implementation-plan.md`
- 阶段目标：完成 GraphRAG 最小闭环，覆盖文本块构图、Neo4j 图谱入库、图检索与向量检索双路召回、聊天图引用和前端最小展示
- 阶段状态：自动化最小闭环、真实 Neo4j API 联调和前端页面快照复核已完成

### 第四阶段步骤记录

1. 第四阶段步骤 1 已完成（2026-04-06）
   - 完成内容：已先补齐并冻结 `phase4-implementation-plan.md`，同步更新 `game-design-document.md`、`tech-stack.md`、`CLAUDE.md` 的第四阶段口径。
   - 验证结果：计划文档已包含目标、边界、状态设计、接口变化、测试要求和本地 Neo4j 联调步骤。
   - 备注：本阶段边界固定为最小 GraphRAG 闭环，不新增独立图谱页面，不暴露 `graph_query` 工具，不接外部知识源，不使用视觉块构图。

2. 第四阶段步骤 2 已完成（2026-04-06）
   - 完成内容：已新增文档图谱摘要字段和数据库迁移，图谱构建使用独立 `GRAPH_BUILD` 任务；文档入库主链成功后异步触发图构建，图失败不回滚文档主状态。
   - 验证结果：`test_graph_tasks.py` 覆盖图任务成功、图任务失败、文档主状态保持 `READY` 等路径。
   - 备注：图谱状态由 `documents.graph_status` 和 graph task 共同观测，文档主 `status` 仍只表示文档入库主链。

3. 第四阶段步骤 3 已完成（2026-04-06）
   - 完成内容：已新增 `backend/infrastructure/graph/`、`graph_service.py` 和图抽取 LLM 适配；三元组抽取支持本地清洗、去空、去重和长度限制，Neo4j 访问使用固定模板。
   - 验证结果：`test_graph_service.py` 覆盖抽取清洗、去重和字段限制。
   - 备注：acceptance 模式已提供确定性图抽取客户端，用于无真实模型环境下的自动化测试。

4. 第四阶段步骤 4 已完成（2026-04-06）
   - 完成内容：`RetrievalService` 已扩展为向量检索与图检索双路召回；关系型问题尝试图检索，Neo4j 不可用或图查询失败时自动降级到向量路径。
   - 验证结果：`test_retrieval_service.py` 覆盖图证据合并和图查询失败降级。
   - 备注：图检索仍是内部检索能力，没有接入 Tool Calling。

5. 第四阶段步骤 5 已完成（2026-04-06）
   - 完成内容：文档详情接口新增 `has_graph`、`graph_status`、`graph_relation_count`；聊天引用新增 `relation_label`、`entity_path`，SSE 沿用原有 `citation` 与 `message_end.citations`。
   - 验证结果：`test_documents_api.py`、`test_chat_api.py`、`test_qa_service.py` 已覆盖图摘要和图引用契约。
   - 备注：没有新增 SSE 事件种类。

6. 第四阶段步骤 6 已完成（2026-04-06）
   - 完成内容：前端服务层、文档 store、聊天 store、文档管理面板和聊天工作台已支持图谱摘要与图引用展示。
   - 验证结果：`documents.spec.ts`、`chat-store.spec.ts`、`chat-workspace.spec.ts` 已覆盖图摘要恢复、图引用恢复和图谱引用卡片展示。
   - 备注：仍不新增独立图谱页面。

7. 第四阶段步骤 7 已完成（2026-04-06）
   - 完成内容：已完成第四阶段自动化回归，并补齐本地 Neo4j 人工联调步骤。
   - 验证结果：
     - `python -m pytest backend/tests -p no:cacheprovider` -> `132 passed`
     - `cmd /c npm run test:unit -- --run` -> `17 passed`
     - `cmd /c npm run typecheck` -> 通过
     - `cmd /c npm run lint` -> 通过
     - `git diff --check -- README.md memory-bank\phase4-implementation-plan.md` -> 通过
   - 备注：自动化基线已覆盖图任务、图检索、图引用、降级路径和前端组件展示。

8. 第四阶段步骤 8 已完成（2026-04-06）
   - 完成内容：已执行真实 Neo4j 本地 API 联调，覆盖 Neo4j 启动、迁移、上传文本烟测文档、图谱构建、图引用问答、删除清理和 Neo4j 不可用降级。
   - 验证结果：
     - `docker run --name rag-neo4j ... neo4j:5-community` 启动成功
     - Neo4j bolt 连接验证通过
     - `alembic upgrade head` 成功应用 `20260406_000004_add_document_graph_summary`
     - 上传 `graph-smoke.txt` 后轮询得到 `task=READY doc=READY graph=READY relations=1`
     - 聊天接口返回 `source_type="graph"`，并包含 `relation_label` 与 `entity_path`
     - 删除文档后 Neo4j 中该文档 `RELATED_TO` 关系数为 `0`
     - Neo4j 停止时重新上传文档得到 `task=READY doc=READY graph=FAILED relations=0`
     - Neo4j 停止时聊天接口仍返回 `success=true`，并降级为文本引用
   - 备注：联调过程中发现并修复了两个真实问题：整句图查询无法命中实体词、图清理异常会阻断文档删除。

9. 第四阶段步骤 9 已完成（2026-04-06）
   - 完成内容：已完成前端页面快照复核，确认历史会话中的图谱引用卡片可渲染。
   - 验证结果：
     - `cmd /c npx --yes --package @playwright/cli playwright-cli -s=phase4 open http://127.0.0.1:5173` 成功打开页面
     - 页面快照确认聊天工作台展示 `图谱引用`
     - 页面快照确认图引用展示 `实体路径：系统 -> related_to -> 用户订单`
     - `playwright-cli -s=phase4 console error` -> `Errors: 0`
   - 备注：最初浏览器 MCP 因 `EPERM: operation not permitted, mkdir 'C:\Windows\System32\.playwright-mcp'` 无法运行，已改用 `playwright-cli` 完成复核。

---

## 第五阶段进展

### 第五阶段概览

- 对应计划：`phase5-implementation-plan.md`
- 阶段目标：完成稳定性与产品化最小闭环，让当前四阶段能力更容易启动、检查、部署、排错和验收
- 阶段状态：实施中

### 第五阶段步骤记录

1. 第五阶段步骤 1 已完成（2026-04-06）
   - 完成内容：新增并冻结 `phase5-implementation-plan.md`，同步更新 `game-design-document.md`、`tech-stack.md`、`CLAUDE.md` 的第五阶段口径。
   - 验证结果：计划文档已明确部署验收、运行检查、健康/就绪检查、配置校验、灰度配置、最低可观测性和测试入口收口要求。
   - 备注：本阶段第一轮固定不做鉴权、登录、多租户，不引入 Kubernetes、完整 CI/CD 平台、Prometheus / Grafana 正式接入；本轮不更新 `architecture.md`，也不进入代码实现。

2. 第五阶段步骤 2 已完成（2026-04-07）
   - 完成内容：新增 `/api/ready` 就绪检查接口、production 环境禁用 `LLM_MODE=acceptance`、新增 `backend/app/services/system_service.py`，并扩展 `scripts/dev.ps1` 的 `.env` 安全检查与 `smoke` 命令入口。
   - 验证结果：
     - `python -m pytest backend/tests -p no:cacheprovider` -> `143 passed`
     - `powershell -ExecutionPolicy Bypass -File scripts/dev.ps1 health` -> 通过
     - `git diff --check` -> 通过（仅 LF/CRLF 提示）
   - 备注：`/api/ready` 将 PostgreSQL、Redis、文件存储定义为必需组件，将 Neo4j 定义为可选组件；可选组件失败返回 `degraded`，不阻断基础文本 RAG 就绪判断。

3. 第五阶段步骤 3 已完成（2026-04-07）
   - 完成内容：补齐 README 中的部署清单、回滚说明、排障说明，并将 `run.py`、`start.bat` 的帮助入口同步支持 `smoke`。
   - 验证结果：
     - `powershell -ExecutionPolicy Bypass -File scripts/dev.ps1 help` -> 通过
     - `powershell -ExecutionPolicy Bypass -File scripts/dev.ps1 status` -> 通过
     - 初次本地 smoke 结果：前端 `5173` 可达，但后端 `/api/health` 与 `/api/ready` 无法连接；结合日志确认 worker 因 Redis `127.0.0.1:6379` 拒绝连接退出，后端卡在 `Waiting for application startup.`，符合外部依赖未启动的阻塞特征
     - 恢复 Docker Desktop、启动 `rag-postgres-pgvector` 与 `rag-redis`、并将本地 `.env` 中 `DATABASE_URL` 端口对齐为 `5433` 后，`powershell -ExecutionPolicy Bypass -File scripts/dev.ps1 smoke` -> 通过
   - 备注：本轮已完成一次真实本地 smoke 验证；当前 `backend`、`frontend`、`worker` 均可运行，`/api/ready` 返回 `ready`，Neo4j 仍按未配置场景走可选降级。

4. 第五阶段步骤 4 已完成（2026-04-07）
   - 完成内容：补齐后端最低可观测性与本地运行产物治理；应用启动阶段新增 `app.startup_started`、`app.startup_completed` 结构化日志，`/api/ready` 新增 `system.readiness_checked` 结构化日志；仓库忽略规则新增 `.playwright-cli/`、`output/`、`data/uploads/`。
   - 验证结果：
     - `python -m pytest backend/tests/test_observability.py -p no:cacheprovider` -> `5 passed`
     - `python -m pytest backend/tests -p no:cacheprovider` -> `145 passed`
     - `powershell -ExecutionPolicy Bypass -File scripts/dev.ps1 smoke` -> 通过
   - 备注：本轮未删除任何本地运行产物，只通过 `.gitignore` 约束避免后续误纳入版本控制；当前 smoke 通过时 `backend`、`frontend`、`worker` 均为运行状态。

5. 第五阶段步骤 5 已完成（2026-04-07）
   - 完成内容：补齐 `worker` 生命周期结构化日志，并为 `scripts/dev.ps1` 新增 `acceptance` 部署验收入口；`smoke` 当前会输出 readiness 组件明细，`acceptance` 会额外检查 `backend/frontend/worker` 进程状态并区分必需组件失败与 Neo4j 可选降级。
   - 验证结果：
     - `python -m pytest backend/tests/test_worker_bootstrap.py -p no:cacheprovider` -> `7 passed`
     - `python -m pytest backend/tests/test_dev_script.py -p no:cacheprovider` -> `2 passed`
     - `python -m pytest backend/tests -p no:cacheprovider` -> `150 passed`
     - `powershell -ExecutionPolicy Bypass -File scripts/dev.ps1 help` -> 通过
     - `powershell -ExecutionPolicy Bypass -File scripts/dev.ps1 health` -> 通过
   - 备注：当前部署验收入口已能明确区分“服务未托管启动”“必需组件未就绪”和“Neo4j 可选降级”三类状态；`run.py` 与 `start.bat` 的帮助入口已同步支持 `acceptance`。

6. 第五阶段步骤 6 已完成（2026-04-07）
   - 完成内容：新增 `scripts/smoke_flow.py` 与 `scripts/dev.ps1 smoke-flow` 主链路烟测入口，真实走”上传文档 -> 轮询任务 READY -> 创建会话 -> 发起问答 -> 校验引用 -> 删除文档”；`run.py`、`start.bat` 和 README 已同步暴露该入口。
   - 验证结果：
     - `python -m pytest backend/tests/test_smoke_flow_script.py -p no:cacheprovider` -> `2 passed`
     - `python -m pytest backend/tests -p no:cacheprovider` -> `152 passed`
     - `powershell -ExecutionPolicy Bypass -File scripts/dev.ps1 help` -> 通过
     - `python run.py help` -> 通过
     - `cmd /c start.bat help` -> 通过
   - 备注：当前主链路 smoke 通过独立 Python helper 承载 HTTP 细节，避免在 PowerShell 中直接堆叠复杂请求组装；`smoke-flow` 会在成功或失败后尝试清理临时上传文档。

7. 第五阶段步骤 7 已完成（2026-04-07）
   - 完成内容：执行第五阶段完整人工验收流程，覆盖 Docker 容器启动、数据库初始化、服务启动、健康检查、就绪检查、端到端烟雾测试和自动化测试套件。
   - 验证结果：
     - Docker Desktop 启动成功
     - PostgreSQL 16 + pgvector 容器创建并运行（端口 5433）
     - Redis 7 容器创建并运行（端口 6379）
     - 数据库表初始化成功
     - 后端服务启动成功（端口 8000）
     - 前端服务运行正常（端口 5173）
     - Worker 服务运行正常
     - `/api/health` 返回 `ok`
     - `/api/ready` 返回所有必需组件就绪，Neo4j 可选降级
     - `python scripts/smoke_flow.py --backend-url http://localhost:8000` -> 通过
     - `python -m pytest backend/tests/ -v --tb=short` -> `150 passed, 2 failed`（2 个失败为 Windows UTF-8 编码问题，非功能缺陷）
   - 备注：第五阶段所有验收标准已满足，产品化最小闭环已成立。

---

## 更新时间线

### 2026-04-03

- 初始化 `progress.md`
- 完成第一阶段步骤 1-6

### 2026-04-04

- 完成第一阶段步骤 7-28

### 2026-04-05

- 完成第一阶段步骤 29
- 第一阶段进入“已验收完成”状态

### 2026-04-06

- 完成第二阶段全部实施与验收
- 更新第二阶段验证基线为后端 `113 passed`、前端 `15 passed`、后端覆盖率 `95%`
- 启动第三阶段
- 新增 `phase3-implementation-plan.md`
- 完成第三阶段最小闭环实现与自动化回归
- 更新当前验证基线为后端 `123 passed`、前端 `16 passed`
- 完成第三阶段人工验收，并补齐验收中发现问题的修复与回归
- 启动第四阶段，新增并冻结 `phase4-implementation-plan.md`
- 完成第四阶段 GraphRAG 自动化最小闭环实现
- 更新当前自动化验证基线为后端 `132 passed`、前端 `17 passed`
- 补齐第四阶段本地 Neo4j 人工联调步骤
- 完成第四阶段真实 Neo4j API 联调和前端页面快照复核
- 合并第四阶段 GraphRAG 最小闭环到本地 `main`
- 启动第五阶段规划，新增并冻结 `phase5-implementation-plan.md`
- 完成第五阶段第一批实现：`/api/ready`、production 配置约束、`dev.ps1 health/smoke`
- 完成第五阶段最低可观测性收口与运行产物忽略规则
- 完成第五阶段部署验收入口与 worker 生命周期日志收口
- 完成第五阶段主链路 smoke 入口与脚本帮助口径同步

### 2026-04-07

- 完成第五阶段完整人工验收流程
- 更新最终验证基线为后端 `150 passed, 2 failed`（2 个失败为 Windows 编码问题）、前端 `19 passed`
- 第五阶段进入"已验收完成"状态

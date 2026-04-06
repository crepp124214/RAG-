# 第四阶段实施计划：GraphRAG 最小闭环

> **阶段状态更新（2026-04-06）：** 本计划用于冻结第四阶段范围、方案和实施顺序。在本计划写定并同步到阶段口径文档前，不进入第四阶段代码实现；阶段进展与验收结果后续统一记录到 `progress.md`。

## 目标

在现有文本 RAG、第二阶段 Tool Calling、第三阶段 PDF 多模态 RAG 基线之上，完成“文本块三元组抽取 -> Neo4j 图谱入库 -> 图检索与向量检索双路召回 -> 聊天图引用返回 -> 前端最小摘要展示”的第四阶段最小闭环。

## 边界

### 本阶段必须实现

- 仅基于已入库文档的文本块构图，不接外部知识源
- 图谱构建采用“文档入库成功后异步构建”，不阻塞文档 `READY`
- 为文档新增图谱摘要能力，如 `has_graph`、`graph_status`、`graph_relation_count`
- 扩展检索与问答编排，支持图检索与向量检索双路召回
- 扩展聊天引用结构，支持图引用
- 在现有前端工作台中展示文档图谱摘要和图引用卡片，不新增独立图谱页面

### 本阶段明确不做

- 独立图谱探索页
- `graph_query` 工具
- 外部知识源补图
- 视觉描述块构图
- 跨文档复杂实体消歧
- 图谱自动本体学习
- Cypher 自由生成式查询
- `python_executor`
- `Celery`
- `Chroma`

## 关键默认值

- 图谱来源固定为当前文档的文本块，忽略视觉块与工具结果
- 文档主状态在文本/多模态入库成功后保持 `READY`
- 图谱构建使用单独 `GRAPH_BUILD` 任务追踪，不把图失败回写为文档 `FAILED`
- 图构建失败时，聊天自动退回纯向量检索
- 单块三元组抽取失败只跳过该块，不中断整篇文档图构建
- 若整篇文档抽不到有效三元组，则图任务标记失败，但不影响现有问答主链
- 图检索不单独暴露为工具，只作为检索编排内部能力
- SSE 不新增事件种类，图证据仍通过 `citation` 与 `message_end.citations` 返回

## 实施顺序

### 步骤 1：扩展图谱任务链路

- 为图谱构建增加独立任务类型 `GRAPH_BUILD`
- 文档文本/多模态入库成功后，异步触发图谱构建任务
- 文档详情摘要支持 `NOT_STARTED / PROCESSING / READY / FAILED`

### 步骤 2：落地图基础设施与抽取服务

- 新增 `backend/infrastructure/graph/`，封装 Neo4j 连接、写入和固定查询模板
- 新增图谱抽取服务，负责把文本块转换为最小三元组
- 本地完成三元组清洗、去空、去重和长度限制

### 步骤 3：扩展数据模型与接口契约

- 扩展 PostgreSQL 中的文档或任务可观测字段，使文档详情能返回图摘要
- 聊天 `citations` 增加图引用最小字段，如 `relation_label`、`entity_path`
- `GET /api/tasks/{task_id}` 支持返回图任务状态

### 步骤 4：扩展检索与问答编排

- 在现有 `RetrievalService` 中加入图检索规划和双路召回
- 图检索仅在关系型、总结型、跨实体型问题时启用
- 图证据与向量证据统一进入重排与提示词上下文
- 图不可用、图超时、图未命中时，稳定降级到现有向量路径

### 步骤 5：接入前端最小闭环

- 文档管理区展示图谱状态、关系数量和构建失败提示
- 聊天引用卡片支持图引用
- 刷新恢复后继续保留图引用事实

### 步骤 6：完成第四阶段验收

- 自动化测试覆盖抽取、图任务、双路召回、API 契约和前端恢复
- 完成 Neo4j 正常、Neo4j 不可用、图任务失败、图检索降级的人工验收
- 实现完成后再同步更新 `architecture.md`、`progress.md` 与 README

## 接口与类型变化

- 文档详情新增：
  - `has_graph`
  - `graph_status`
  - `graph_relation_count`
- 任务详情支持图任务：
  - `task_type = GRAPH_BUILD`
- 聊天引用结构新增图引用字段：
  - `source_type = "graph"`
  - `relation_label`
  - `entity_path`

## 测试要求

- 图谱抽取：
  - 正常文本抽取出合法三元组
  - 空文本和低质量文本返回空结果
  - 重复三元组被去重
  - 单块抽取失败不打断整篇处理
- 图任务链路：
  - 入库成功后可触发图构建
  - 图任务成功不改变文档 `READY`
  - 图任务失败不影响纯向量问答
- 检索问答：
  - 事实问题只走向量路径
  - 关系型问题触发双路召回
  - 图命中和向量命中可混合返回
  - 图超时、图未命中、Neo4j 不可用时稳定降级
- API 契约：
  - 文档详情包含图摘要字段
  - 图任务可查询
  - 聊天 `citations` 支持图引用
  - SSE 与刷新恢复保留图引用
- 前端：
  - 文档区图摘要展示
  - 图引用卡片展示
  - 刷新恢复

## 本地 Neo4j 联调步骤

> 本节用于第四阶段人工验收。自动化测试可以在无 Neo4j 的环境中通过，但本地端到端联调必须启动真实 Neo4j，确认图写入、图检索和降级路径都真实生效。

### 前置条件

- 已安装 Python 依赖：`pip install -r requirements.txt`
- 已安装前端依赖：`cd frontend && npm install`
- 本地 PostgreSQL 与 Redis 按现有开发流程可用
- 本地可运行 Docker，或已有可访问的 Neo4j 5.x 实例
- 若使用真实模型抽取，必须配置有效 `DASHSCOPE_API_KEY`
- 若只做本地链路烟测，可设置 `LLM_MODE=acceptance`，但仍需提供占位 `DASHSCOPE_API_KEY=test-key` 通过配置校验

### 启动 Neo4j

如果本机没有现成 Neo4j，可用 Docker 启动社区版：

```powershell
docker run --name rag-neo4j `
  -p 7474:7474 `
  -p 7687:7687 `
  -e NEO4J_AUTH=neo4j/ragtest123 `
  neo4j:5-community
```

如果容器已存在，可改用：

```powershell
docker start rag-neo4j
```

浏览器打开 `http://127.0.0.1:7474`，使用 `neo4j / ragtest123` 登录，确认 Neo4j 可访问。

### 配置环境变量

在仓库根目录 `.env` 中补齐第四阶段图谱配置：

```dotenv
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=ragtest123
GRAPH_QUERY_LIMIT=5
```

如果只做无真实模型的本地烟测，可同时设置：

```dotenv
LLM_MODE=acceptance
DASHSCOPE_API_KEY=test-key
```

如果要验证真实抽取质量，则保持 `LLM_MODE=production`，并设置真实 `DASHSCOPE_API_KEY`。

### 应用数据库迁移

启动服务前先应用文档图谱摘要字段迁移：

```powershell
alembic upgrade head
```

迁移完成后，`documents` 表应包含：

- `graph_status`
- `graph_relation_count`

### 启动本地服务

按现有开发入口启动全链路：

```powershell
start.bat dev
```

如果需要分开启动，至少需要三个进程：

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
python -m worker.main
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

### 上传包含明确关系的文档

准备一个 `graph-smoke.txt`：

```text
系统 A 依赖 系统 B。
系统 B 调用 数据库 C。
数据库 C 存储 用户订单。
```

通过前端上传，或使用接口上传：

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/documents/upload `
  -F "file=@graph-smoke.txt"
```

记录返回的 `document_id` 和 `task_id`。

### 观察入库与图谱状态

先确认 ingestion 任务进入 `READY`：

```powershell
curl.exe http://127.0.0.1:8000/api/tasks/<task_id>
```

再轮询文档详情，确认图谱状态从 `NOT_STARTED` 或 `PROCESSING` 进入 `READY`：

```powershell
curl.exe http://127.0.0.1:8000/api/documents/<document_id>
```

期望结果：

- `data.status` 保持 `READY`
- `data.graph_status` 最终为 `READY`
- `data.has_graph` 为 `true`
- `data.graph_relation_count` 大于 `0`

如果需要查看图任务记录，可在数据库中查询：

```sql
select id, task_type, status, error_message
from tasks
where document_id = '<document_id>'
order by created_at desc;
```

### 验证 Neo4j 中存在图数据

在 Neo4j Browser 中执行：

```cypher
MATCH (s:Entity)-[r:RELATED_TO]->(o:Entity)
WHERE r.document_id = '<document_id>'
RETURN s.name, r.predicate, o.name, r.chunk_id, r.page_number
LIMIT 20;
```

期望至少返回一条关系，并且 `document_id`、`chunk_id`、`page_number` 可追踪来源。

### 验证聊天双路召回

先创建会话：

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/chat/sessions
```

记录 `session_id`，再提关系型问题：

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/chat/query `
  -H "Content-Type: application/json" `
  -d "{\"session_id\":\"<session_id>\",\"query\":\"系统 A 和系统 B 之间是什么关系？\"}"
```

期望结果：

- `data.citations` 中至少存在一条 `source_type = "graph"` 的引用
- 图引用包含 `relation_label`
- 图引用包含 `entity_path`
- 回答仍可同时包含文本向量证据

### 验证前端展示

打开 `http://127.0.0.1:5173`，确认：

- 文档管理区显示图谱状态和图谱关系数
- 图谱构建失败时显示失败提示，但文档仍可问答
- 聊天引用卡片中 `source_type = "graph"` 显示为“图谱引用”
- 图引用显示实体路径和来源页码
- 刷新页面后，历史消息中的图引用仍可恢复

### 验证 Neo4j 不可用降级

停止 Neo4j：

```powershell
docker stop rag-neo4j
```

重启后端和 worker，再上传新文档或提出关系型问题。

期望结果：

- 已完成文本入库的文档主状态不被图失败改成 `FAILED`
- 图构建任务或文档图谱摘要可进入 `FAILED`
- 聊天接口不因图查询失败报主链错误
- 仍能基于向量检索返回普通文本 RAG 回答

验证完成后重新启动 Neo4j：

```powershell
docker start rag-neo4j
```

### 验证删除文档清理图数据

删除刚才上传的文档：

```powershell
curl.exe -X DELETE http://127.0.0.1:8000/api/documents/<document_id>
```

再到 Neo4j Browser 执行：

```cypher
MATCH (s:Entity)-[r:RELATED_TO]->(o:Entity)
WHERE r.document_id = '<document_id>'
RETURN count(r) AS relation_count;
```

期望 `relation_count = 0`。如果有孤立实体节点，也应在清理流程中被删除。

## 完成标准

- 文档完成入库后可以异步构建图谱，不阻塞文档 `READY`
- 关系型问题可以命中图证据并返回图引用
- 图构建失败时，文本与多模态问答行为不回退
- 文档详情与任务详情可以观察图构建状态
- 前端刷新后图摘要与图引用仍可恢复

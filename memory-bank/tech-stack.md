# RAG 智能文档检索助手技术栈推荐

## 1. 结论

本项目当前最合适、最简单、且相对健壮的技术栈建议选择：

- 前端：Vue 3 + Vite + Element Plus + Pinia
- 后端：FastAPI + Pydantic + Uvicorn
- 异步任务：RQ + Redis
- 元数据存储：PostgreSQL
- 向量检索：pgvector
- 模型接入：DashScope / 通义千问（Qwen）
- 多模态解析：PyMuPDF + pdfplumber
- 部署方式：Docker Compose

第一阶段冻结实现口径：

- 单用户、无登录、无鉴权、无多租户
- ORM 与迁移：`SQLAlchemy + Alembic`
- 文档去重策略：重复上传提示“已存在”，不重复入库
- 删除策略：硬删除
- 任务模型：一文档多任务
- 会话标题：首条问题自动截断生成
- 后端测试：`pytest`
- 前端测试：`vitest + vue-test-utils`
- 旧 `core/` 迁移方式：尽量直接复用后包一层

这套方案的核心特点是：

- 足够简单，容易从当前 Streamlit Demo 平滑迁移
- 足够稳健，核心组件都很成熟
- 足够实用，能支撑 RAG 产品第一阶段上线
- 后续可逐步扩展 Tool Calling、多模态、GraphRAG

---

## 2. 为什么推荐这套方案

你的项目现在虽然希望支持很多高级能力，但你也明确说了功能可以逐步添加。因此最优先的不是“一次把所有技术都上满”，而是先选一套：

- 容易开发
- 容易部署
- 容易排错
- 容易演进

相比 `Celery + Neo4j + Chroma/Milvus` 这样的组合，第 2 套方案明显更轻：

- `RQ` 比 `Celery` 更简单，适合中小型异步任务链路
- `PostgreSQL + pgvector` 可以同时承担业务数据和向量检索，减少组件数量
- 不急着引入 `Neo4j`，先把核心 RAG 问答、上传、异步入库、会话系统做扎实

对当前阶段来说，这样更符合“简单优先、稳健优先”的目标。

---

## 3. 推荐技术栈明细

## 3.1 前端

### Vue 3

用途：

- 构建主 Web 界面
- 替代当前 Streamlit 前端

原因：

- 生态成熟
- 中文社区资料多
- 适合中后台产品和聊天工作台场景

### Vite

用途：

- 前端构建工具

原因：

- 启动快
- 配置轻
- 和 Vue 3 配合非常成熟

### Element Plus

用途：

- UI 组件库

原因：

- 很适合文档管理、会话列表、上传面板、表格、任务状态页
- 组件齐全，开发效率高

### Pinia

用途：

- 前端状态管理

原因：

- 比 Vuex 更轻
- 更适合 Vue 3
- 管理聊天状态、任务状态、文档状态都比较顺手

---

## 3.2 后端

### FastAPI

用途：

- 提供 REST API
- 提供 SSE 流式响应接口
- 承载聊天、文档上传、任务查询、会话管理等服务

原因：

- Python 生态里最适合做 AI API 服务的框架之一
- 类型提示和接口文档体验很好
- 和异步、流式输出结合方便

### Pydantic

用途：

- 请求响应模型定义
- 配置校验
- 数据结构约束

原因：

- 和 FastAPI 原生契合
- 适合保证接口输入输出规范

### Uvicorn

用途：

- FastAPI 运行服务

原因：

- 标准方案
- 简单稳定

---

## 3.3 异步任务

### RQ + Redis

用途：

- 文档上传后的异步解析
- 向量化入库
- 长耗时任务执行

原因：

- 比 Celery 更容易理解和维护
- 对于你的第一阶段文档任务队列已经足够
- 配置少、排障简单

适合承担的任务：

- 文档解析
- 文本切块
- 图片抽取
- Embedding
- 向量入库

暂时不适合的场景：

- 非常复杂的任务编排
- 多级任务依赖图
- 大规模分布式任务系统

但对当前项目完全够用。

---

## 3.4 数据存储

### PostgreSQL

用途：

- 存储业务元数据
- 存储会话、消息、文档、任务状态
- 配合 `pgvector` 存储向量

原因：

- 成熟稳定
- 一个数据库能承载多类数据
- 运维难度低于“关系库 + 独立向量库”双系统

建议存储内容：

- 用户信息
- 会话与消息
- 文档元数据
- 文档处理任务状态
- chunk 元数据
- 向量数据

### pgvector

用途：

- 在 PostgreSQL 中进行向量存储与近邻检索

原因：

- 省掉独立向量数据库组件
- 简化部署和备份
- 对中小规模知识库足够实用

适合当前项目的原因：

- 你现在还在重构阶段，不适合过早引入重型基础设施
- `pgvector` 能很好支撑第一阶段产品化

---

## 3.5 模型层

### DashScope / 通义千问（Qwen）

用途：

- 对话生成
- Tool Calling
- 多模态理解的后续接入

原因：

- 你项目现有基础就是通义千问
- 连续性最好，迁移成本最低
- 后续扩展 Tool Calling 与 Qwen-VL 也最顺

建议模型分工：

- 主聊天模型：Qwen-Plus 或适合成本/效果平衡的通义模型
- Embedding：DashScope Embedding
- 后续多模态：Qwen-VL

---

## 3.6 文档解析

### PyMuPDF

用途：

- PDF 文本提取
- 页面结构信息读取
- 图片提取

原因：

- 速度快
- 对 PDF 处理能力强
- 适合作为主解析工具

### pdfplumber

用途：

- 辅助处理复杂版式、表格、文本块位置

原因：

- 在精细化文档结构提取方面很有价值
- 可以作为 PyMuPDF 的补充

建议策略：

- 第一阶段：优先用 `PyMuPDF`
- 第二阶段：遇到复杂表格和版面需求时再引入 `pdfplumber`

---

## 3.7 部署

### Docker Compose

用途：

- 本地开发
- 测试环境
- 小规模部署

原因：

- 容易启动整套服务
- 易于协作和复现环境
- 适合当前项目体量

建议容器：

- `frontend`
- `backend`
- `worker`
- `redis`
- `postgres`

---

## 4. 不推荐现在就上的技术

### Celery

原因：

- 功能强，但复杂度明显高于 `RQ`
- 你当前项目优先级是快速稳定落地，而不是大规模任务编排

### Chroma

原因：

- 适合 Demo 和单机试验
- 但长期演进里，统一收敛到 PostgreSQL + pgvector 更简单

### Milvus

原因：

- 更偏重型向量平台
- 当前阶段会增加部署与运维成本

### Neo4j

原因：

- 只有在你正式进入 GraphRAG 阶段时才真正需要
- 现在先不上，可以减少一个数据库系统

---

## 5. 分阶段演进建议

## Phase 1：先搭稳底座

先落以下技术：

- Vue 3 + Vite + Element Plus + Pinia
- FastAPI + Pydantic
- PostgreSQL + pgvector
- RQ + Redis
- DashScope / Qwen
- PyMuPDF

目标：

- 替换掉 Streamlit
- 完成前后端解耦
- 完成异步文档入库
- 完成基础聊天与检索

## Phase 2：补 Tool Calling

增加：

- 工具注册机制
- `web_search`
- `document_lookup`
- 后续再考虑 `python_executor`

目标：

- 让系统在知识库不足时能联网或查内部状态

## Phase 3：补多模态

增加：

- 图片抽取
- 页面坐标信息
- Qwen-VL
- 混合 chunk 构建

目标：

- 支持图表和图片内容检索

## Phase 4：再上 GraphRAG

增加：

- Neo4j
- 三元组抽取
- 图谱检索

目标：

- 支持跨文档、跨实体、全局关系问题

---

## 6. 最终推荐版本

如果只给一个最终结论，我推荐你现在就按下面这套落地：

```text
Frontend:
- Vue 3
- Vite
- Element Plus
- Pinia

Backend:
- FastAPI
- Pydantic
- Uvicorn

Async:
- RQ
- Redis

Database:
- PostgreSQL
- pgvector

LLM:
- DashScope / Qwen
- DashScope Embedding

Parsing:
- PyMuPDF

Deploy:
- Docker Compose
```

这套技术栈最符合你当前项目的三个核心要求：

- 最合适：和你现有 Python RAG 代码衔接自然
- 最简单：组件数量少，心智负担低
- 最健壮：关键部件都成熟，适合逐步迭代

---

## 7. 一句话建议

先把系统做成“FastAPI + Vue + PostgreSQL + pgvector + RQ + Redis”的稳定产品底座，再逐步往上叠加 Tool Calling、多模态和 GraphRAG，这比一开始把所有高级能力一起塞进系统更稳。


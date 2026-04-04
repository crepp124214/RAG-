# RAG 智能文档检索助手

## 项目简介

这是一个正在从 Streamlit 演示项目逐步重构为产品化系统的 RAG 智能文档检索助手。

当前项目的目标不是继续叠加 Demo 功能，而是先完成第一阶段的“稳定底座”和“最小可运行产品”，建立清晰、可扩展、可测试、可维护的工程结构。

当前已经确认的第一阶段技术路线为：

- 前端：Vue 3 + Vite + Element Plus + Pinia
- 后端：FastAPI + Pydantic + Uvicorn + SQLAlchemy
- 异步任务：RQ + Redis
- 数据层：PostgreSQL + pgvector
- 模型层：DashScope / 通义千问（Qwen）+ DashScope Embedding + BGE Reranker
- 文档解析：PyMuPDF
- 部署方式：Docker Compose

---

## 当前阶段目标

第一阶段只聚焦最小可运行产品，目标是打通以下完整链路：

- 文档上传
- 异步文档解析
- 文本分块
- 向量化入库
- 检索增强问答
- 会话与消息持久化
- SSE 流式输出

---

## 第一阶段明确不做

以下能力不属于当前阶段范围：

- Tool Calling
- `web_search`
- `document_lookup`
- `python_executor`
- 多模态主链路
- Qwen-VL
- Neo4j
- GraphRAG
- WebSocket
- 权限系统
- 多租户

---

## 当前仓库状态

当前仓库仍保留旧版 Streamlit 结构，主要用于迁移参考：

- `app.py`
- `core/`
- `chroma_db/`

后续主架构目标目录为：

```text
frontend/
backend/
worker/
docs/
scripts/
tests/
```

说明：

- 旧 `app.py` 和 `core/` 仅作为迁移来源
- 新能力不应继续堆积在旧结构中

---

## 核心文档

请优先阅读以下文档：

- [RAG-design-document.md](D:\agent开发项目\RAG智能文档检索助手\RAG-design-document.md)
- [tech_stack.md](D:\agent开发项目\RAG智能文档检索助手\tech_stack.md)
- [implementation-plan.md](D:\agent开发项目\RAG智能文档检索助手\implementation-plan.md)
- [CLAUDE.md](D:\agent开发项目\RAG智能文档检索助手\CLAUDE.md)
- [AGENTS.md](D:\agent开发项目\RAG智能文档检索助手\AGENTS.md)

它们的作用分别是：

- `RAG-design-document.md`：系统级设计蓝图
- `tech_stack.md`：技术栈选择依据
- `implementation-plan.md`：第一阶段实施计划
- `CLAUDE.md`：项目最高优先级规则
- `AGENTS.md`：AI/开发者协作与交接规则

---

## 推荐开发顺序

默认按以下顺序推进：

1. 设计新目录结构
2. 搭建 FastAPI 后端骨架
3. 搭建 Vue 3 前端骨架
4. 接入 PostgreSQL + pgvector
5. 接入 RQ + Redis
6. 打通文档上传与异步入库
7. 打通基础检索问答
8. 完成会话与消息持久化
9. 完成 SSE 流式输出

---

## 开发原则

项目开发必须遵守以下原则：

- 先设计，后编码，最后验证
- 优先小步迭代，不做一次性大爆炸改造
- 命名语义化
- 单一职责
- DRY
- KISS
- 配置与代码分离
- 错误处理不可吞异常
- 测试必须覆盖失败路径

---

## 当前仓库文件说明

### 现有文件

- `app.py`：旧版 Streamlit 主入口
- `run.py`：旧版运行辅助脚本
- `start.bat`：Windows 启动脚本
- `core/`：旧版核心逻辑
- `scripts/`：迁移辅助脚本

### 新增规范文件

- `CLAUDE.md`：项目级规则、阶段边界、开发规范
- `AGENTS.md`：代理分工、交接与验收规范
- `RAG-design-document.md`：系统架构设计文档
- `tech_stack.md`：技术栈推荐文档
- `implementation-plan.md`：实施计划文档

---

## 环境与配置

当前项目仍处于重构前期，配置方式正在从旧结构迁移到新结构。

第 3 步已经冻结了统一配置入口，当前约定如下：

- 根目录使用 `.env.example` 作为全项目变量示例
- `backend/.env.example` 只保留后端所需变量
- `frontend/.env.example` 只保留前端所需变量
- 后端统一从 `backend/app/settings/config.py` 读取配置
- 前端统一从 `frontend/src/config/env.ts` 读取 `VITE_API_BASE_URL`

第一阶段后端关键环境变量：

- `APP_ENV`
- `DATABASE_URL`
- `REDIS_URL`
- `DASHSCOPE_API_KEY`
- `FILE_STORAGE_PATH`

第一阶段已冻结的默认配置：

- `CHUNK_SIZE=800`
- `CHUNK_OVERLAP=150`
- `VECTOR_TOP_K=12`
- `RERANK_TOP_N=5`

说明：

- 缺少关键后端变量时，配置加载必须失败并给出明确错误
- 前端默认 API 地址为 `http://127.0.0.1:8000`
- 旧 `core/` 中零散读取环境变量的方式后续将逐步迁移到统一配置模块

---

## 测试与验证要求

第一阶段所有开发都必须满足：

- 核心逻辑有单元测试
- 接口与数据库交互有集成测试
- 至少保留一条“上传 -> 入库 -> 问答”的主链路测试
- 成功路径和失败路径都必须验证

---

## 当前最重要的约束

如果你要继续开发这个仓库，请先记住这几点：

- 不要把第一阶段做成大而全平台
- 不要提前引入 Tool Calling、多模态、GraphRAG
- 不要继续把长期架构堆在 Streamlit 旧结构上
- 不要脱离 `CLAUDE.md`、`AGENTS.md`、设计文档和实施计划擅自发挥

---

## 后续建议

在当前基础上，最值得优先推进的是：

- 建立 `frontend/`、`backend/`、`worker/` 目录骨架
- 补齐 `.env.example`
- 建立 FastAPI 基础应用
- 建立 Vue 3 基础工作台
- 开始第一阶段实施计划中的任务 1 到任务 5


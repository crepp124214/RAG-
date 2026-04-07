# 第五阶段实施计划：产品化最小闭环

## 1. 阶段目标

第五阶段冻结为“稳定性与产品化最小闭环”。

本阶段不继续扩展 RAG 能力，而是让已完成的四阶段能力更容易启动、检查、部署、排错和验收。当前基线已经包含：

- 第一阶段：文本 RAG 稳定底座
- 第二阶段：Tool Calling 最小闭环
- 第三阶段：PDF 多模态 RAG
- 第四阶段：GraphRAG 最小闭环

第五阶段的第一交付物是本计划文档和阶段口径同步。计划文档冻结前不得直接进入实现；本轮只做文档规划，不写后端、前端或脚本代码。

## 2. 阶段边界

本阶段默认包含：

- 部署验收清单
- 运行检查脚本规划
- 健康检查与就绪检查规划
- 配置校验与 `.env.example` 口径治理
- 灰度配置说明
- 最低可观测性口径
- 测试入口与人工验收入口收口
- 本地运行产物的忽略与清理策略规划

本阶段默认不包含：

- 鉴权、登录、多租户
- Kubernetes
- 完整 CI/CD 平台
- Prometheus / Grafana 正式接入
- 新 RAG 能力
- `python_executor`
- 独立图谱探索页
- `graph_query` 工具
- 外部知识源补图
- 自动删除本地运行产物

如后续确实需要鉴权、重型监控或正式部署平台，应单独形成后续阶段或子计划，不混入当前最小闭环。

## 3. 固定交付物

### 3.1 健康与就绪检查

- 保留 `/api/health` 作为轻量存活检查。
- 后续实现阶段新增或明确 `/api/ready` 作为就绪检查。
- `/api/ready` 应检查：
  - PostgreSQL 连接
  - Redis 连接
  - 本地文件存储目录可写性
  - Neo4j 可选连接状态
- Neo4j 在第五阶段仍是可选依赖；缺失时应返回可理解的降级状态，不阻断基础文本 RAG 就绪判断。

### 3.2 运行检查脚本

后续实现阶段新增或扩展 `health` / `check` / `smoke` 类脚本，优先复用现有 `scripts/dev.ps1`。

脚本应覆盖：

- Python 环境与后端依赖
- Node 环境与前端依赖
- PostgreSQL 可达性
- Redis 可达性
- Neo4j 可选可达性
- 后端基础启动条件
- 前端基础启动条件
- 迁移状态提示

脚本不得在未确认的情况下删除用户本地文件。

### 3.3 配置治理

后续实现阶段应整理 `.env.example`、README 和配置校验规则。

配置口径固定为：

- production 环境不应使用 `LLM_MODE=acceptance`。
- Search、Multimodal、Neo4j 均应通过显式环境变量或配置项进行灰度开关。
- Neo4j 缺失时允许 GraphRAG 降级，但必须在就绪检查和日志中清晰呈现。
- 关键配置缺失时应给出可定位错误，不使用隐式 fallback 冒充正式集成。

### 3.4 部署验收说明

第五阶段优先支持 Docker Compose / Windows 脚本路线，不引入 Kubernetes。

后续实现与文档应补齐：

- 依赖安装
- 环境变量配置
- 数据库迁移
- 后端启动
- worker 启动
- 前端启动
- Neo4j 可选启动
- 上传文档烟测
- 聊天烟测
- 回滚说明
- 常见故障定位

### 3.5 最低可观测性

本阶段只定义最低可观测性，不接入重型监控平台。

最低口径包括：

- 继续使用现有结构化日志与 `request_id`
- 关键后台任务需要记录开始、成功、失败和耗时
- readiness 检查失败需要给出组件级状态
- README 或运维文档中列出需要关注的错误模式和排查入口

Prometheus / Grafana 如需正式接入，应进入后续单独阶段。

### 3.6 本地运行产物策略

当前仓库可能出现 `.playwright-cli/`、`data/uploads/`、`output/` 等本地运行产物。

第五阶段只规划忽略或清理策略：

- 可以补充 `.gitignore` 或清理脚本。
- 清理脚本必须默认安全，不自动删除用户未确认的文件。
- 本轮规划阶段不删除任何本地运行产物。

## 4. 实施顺序

1. 新增并冻结 `memory-bank/phase5-implementation-plan.md`。
2. 同步 `CLAUDE.md`、`memory-bank/game-design-document.md`、`memory-bank/tech-stack.md`、`memory-bank/progress.md` 的阶段口径。
3. 进入实现前，先补配置与 readiness 相关测试。
4. 实现 `/api/ready` 与配置校验。
5. 扩展或新增 smoke/check 脚本。
6. 补齐部署验收、故障定位和最低可观测性文档。
7. 执行自动化回归和人工烟测。
8. 验证完成后再同步 `architecture.md` 与最终 `progress.md` 实现状态。

## 5. 测试要求

文档阶段验证：

- `memory-bank/phase5-implementation-plan.md` 存在。
- 阶段口径文档一致，当前阶段从第四阶段收口切到第五阶段规划。
- 文档明确不做鉴权、不做多租户、不引入 Kubernetes、不接入 Prometheus/Grafana 正式监控平台。

后续实现阶段验证：

- 后端：`python -m pytest backend\tests -p no:cacheprovider`
- 前端：`cmd /c npm run test:unit -- --run`
- 前端类型检查：`cmd /c npm run typecheck`
- 前端 lint：`cmd /c npm run lint`
- 运维脚本：在 Neo4j 缺失时给出可理解降级结果，在配置完整时通过。
- 人工验收：从干净环境按 README 启动服务、应用迁移、上传文档、完成一次聊天、检查健康和就绪结果。

## 6. 假设

- 本地 `main` 已合并第四阶段，可作为第五阶段规划基线。
- Neo4j 在第五阶段仍是可选依赖，缺失时不阻断基础文本 RAG。
- 本阶段第一交付物是计划文档，不直接进入实现。
- `architecture.md` 只记录已真实落地的架构事实，因此第五阶段实现完成并验证前暂不更新。

# 开发执行计划

项目：企业需求与合同履约智能客服平台（`enterprise-support-agent`）

## 交付原则

- 按阶段小步开发，每次只实现一个明确阶段。
- 每个阶段完成后运行与本阶段相关的验证并修复问题。
- 不提前实现后续阶段能力。
- Java 业务服务保持 Controller、Service、Repository 分层；Service 只依赖 Repository 抽象。
- Python 服务所有业务数据均通过 Java HTTP Client 获取，不直接访问数据库。
- 当前以只读需求查询为唯一业务范围。
- Git 提交由项目维护者执行；Codex 不执行 Git 操作。

## 当前范围

已支持：

- 需求编号精确查询
- 组合条件查询与分页
- 需求当前进度查询
- 默认内存数据模式
- MySQL/MyBatis-Plus/Flyway 可选数据模式
- Python 异步 Java 后端 Client

当前明确不包含：

- 合同、订单和履约业务模块
- 创建、修改、审批和删除需求
- RAG、向量数据库、MCP、多 Agent
- Redis、消息队列、分布式事务
- 登录认证和正式前端
- 自然语言 SQL

## 阶段计划与状态

| 阶段 | 目标 | 状态 | 建议提交信息 |
| --- | --- | --- | --- |
| 1 | Monorepo、Java/Python 骨架、健康检查 | 已完成 | `chore: 初始化 Monorepo 项目骨架` |
| 2 | 需求领域模型、内存 Repository、三个查询 API | 已完成 | `feat: 添加内存需求查询接口` |
| 3 | MyBatis-Plus、MySQL Profile、Flyway、Docker Compose、Testcontainers | 已完成 | `feat: 添加 MySQL 需求仓储实现` |
| 4 | Python 配置、Pydantic 模型、Java RequirementClient | 已完成 | `feat: 添加需求后端 Client` |
| 5 | 需求查询 Agent 工具 | 已完成 | `feat: 添加需求查询工具` |
| 6 | DeepSeek 与 LangGraph Agent | 已完成 | `feat: 添加 DeepSeek 需求查询 Agent` |
| 7 | FastAPI 聊天接口与端到端联调 | 已完成 | `feat: 开放需求 Agent 聊天接口` |

## 已完成阶段的验收记录

### 阶段 1

- Java 使用 JDK 25 和 Spring Boot 4.1.0。
- Python 项目声明使用 Python 3.14 和 uv。
- Java、Python 健康检查已建立。

### 阶段 2

- 默认 `local` Profile 使用 12 条内存需求数据，不连接数据库。
- 三个 Java 查询接口均返回统一 `ApiResponse`。
- 具备 traceId、分页、参数校验和全局异常处理。

### 阶段 3

- `mysql` Profile 使用 MyBatis-Plus Repository；Controller/Service 接口未改变。
- Flyway 通过 `V1__create_requirements.sql` 创建表并初始化数据。
- Docker Compose 提供 MySQL 8.4。
- Testcontainers 集成测试已编写；当前开发环境没有 Docker，因此相关测试会跳过。

### 阶段 4

- Python `RequirementClient` 支持详情、组合查询和进度三个 Java API。
- 使用异步 `httpx`，支持注入 Client/MockTransport。
- Java camelCase 与 Python snake_case 自动转换。
- `uv.lock` 应在 Python 环境中执行 `uv lock` 后更新。

### 阶段 5

- `ToolExecutionResult` 区分成功、无结果和失败。
- 三个查询工具只调用 `RequirementClient`，不直接访问数据库。
- 输入参数使用 Pydantic 校验；后端异常不暴露 URL、堆栈或连接详情。
- mock 测试覆盖成功、无结果、参数错误、需求不存在和后端不可用。

## 下一阶段：阶段 7

目标是提供 FastAPI `/chat`，接入 session 上下文并完成 Agent → Java 的端到端联调。

阶段 7 验收前的 Python 验证命令：

```bash
cd agent
uv lock
uv run pytest
uv run ruff check .
uv run mypy app tests
```

## 后续阶段概要

### 阶段 6：DeepSeek 与 LangGraph Agent

- 使用 OpenAI-compatible DeepSeek Client。
- 缺少 API Key 时，仅 Agent 调用返回明确配置错误；健康检查继续可用。
- 实现意图判断、工具选择、工具结果处理、自然语言回答和基础多轮上下文。
- LLM 必须可 mock；自动化测试不得调用真实 DeepSeek。

### 阶段 7：聊天接口与端到端联调

- 提供 FastAPI `POST /chat`。
- 请求包含 `userId` 和 `sessionId`。
- Agent 通过工具调用 Java 后端。
- 补充启动说明、curl 示例、端到端测试和常见错误说明。

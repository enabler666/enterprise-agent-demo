# 开发执行计划

本文是开发阶段状态与验收记录的权威来源，不承担启动说明或 API 文档职责。项目当前仅支持只读需求查询。

## 执行原则

- 每次只实现一个阶段，完成并汇报验证结果后停止，等待维护者明确继续。
- Java 保持 Controller、Service、Repository 分层，Service 只依赖 Repository 抽象。
- Python 业务数据只通过 Java HTTP API 获取，不直接访问数据库。
- Git 操作和 Python 环境验证由维护者执行。
- 不提前加入需求写操作、合同、订单、认证、RAG、向量数据库、MCP、多 Agent 或自然语言 SQL。

## 阶段状态

| 阶段 | 目标 | 状态 | 建议提交信息 |
| --- | --- | --- | --- |
| 1 | Monorepo、Java/Python 骨架、健康检查 | 已完成 | `chore: 初始化 Monorepo 项目骨架` |
| 2 | 需求领域模型、内存 Repository、三个查询 API | 已完成 | `feat: 添加内存需求查询接口` |
| 3 | MyBatis-Plus、MySQL Profile、Flyway、Docker Compose、Testcontainers | 已完成 | `feat: 添加 MySQL 需求仓储实现` |
| 4 | Python 配置、Pydantic 模型、Java RequirementClient | 已完成 | `feat: 添加需求后端 Client` |
| 5 | 需求查询 Agent 工具 | 已完成 | `feat: 添加需求查询工具` |
| 6 | DeepSeek 与 LangGraph Agent | 已完成 | `feat: 添加 DeepSeek 需求查询 Agent` |
| 7 | FastAPI 聊天接口与端到端联调 | 待验收 | `feat: 开放需求 Agent 聊天接口` |

阶段 1–6 已完成。阶段 7 的实现文件已经存在，但按仓库贡献规则仍是下一阶段，必须由维护者执行 Python 环境验证并明确确认后，才能标记为已完成。不得提前规划或实现阶段 8。

## 验收摘要

- 阶段 1–3：建立 Java 25、Spring Boot 4.1.0 和 Python 3.14 工程；完成健康检查、统一响应、traceId、三个只读查询 API，以及可切换的内存/MySQL Repository。MySQL 集成测试依赖 Docker。
- 阶段 4–5：实现异步 `RequirementClient` 和三个只读查询工具；支持 Pydantic 校验、camelCase/snake_case 转换，以及成功、无结果和安全错误结果。
- 阶段 6：实现可 mock 的 DeepSeek + LangGraph Agent、工具选择、最多三轮工具调用和基础多轮上下文；自动化测试不调用真实模型。
- 阶段 7（待验收实现）：提供 `POST /chat`、进程内会话存储、端到端 mock 测试、启动说明和联调示例。

详细 API 行为见 [requirement-api.md](requirement-api.md)，当前跨模块实现见 [current-flow.md](current-flow.md)。

## 维护者验证命令

Java：

```powershell
cd backend
./mvnw.cmd clean verify
```

Python：

```bash
cd agent
uv lock
uv run pytest
uv run ruff check .
uv run mypy app tests
```

若 Docker 不可用，Testcontainers 测试可以跳过，但验收记录必须明确说明。

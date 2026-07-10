# Enterprise Support Agent Service

当前完成到阶段 5：提供 FastAPI 健康检查、异步 Java `RequirementClient` 和只读需求查询工具。尚未实现 LLM、LangGraph 主流程或聊天接口。

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

## 后端 Client

`app.clients.RequirementClient` 封装了 Java 后端的三个只读接口：

- `get_requirement_by_no`
- `search_requirements`
- `get_requirement_progress`

配置全部来自环境变量：

```text
DEEPSEEK_API_KEY
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
BACKEND_BASE_URL=http://localhost:8080
BACKEND_TIMEOUT_SECONDS=10
```

Client 使用 `httpx.AsyncClient`，支持依赖注入和 `MockTransport` 测试，不会在模块导入时创建网络连接。Java API 约定见 [需求查询 API](../docs/requirement-api.md)。

## 查询工具

当前还提供 `RequirementTools`，把 Java Client 包装为后续 Agent 可复用的只读工具：

- `get_requirement_by_no`
- `search_requirements`
- `get_requirement_progress`

三个工具接收 Pydantic 校验后的输入，并统一返回 `ToolExecutionResult`：

| 状态 | 含义 |
| --- | --- |
| `SUCCESS` | 查询成功，`data` 包含结构化结果 |
| `NO_RESULT` | 没有匹配数据或指定需求不存在 |
| `ERROR` | 参数不合法或后端不可用/协议异常 |

工具不会访问数据库，也不暴露 Java URL、内部堆栈或连接错误细节。

测试与静态检查：

```bash
uv lock
uv run pytest
uv run ruff check .
uv run mypy app tests
```

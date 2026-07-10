# Enterprise Support Agent Service

当前完成到阶段 4：提供 FastAPI 健康检查，以及调用 Java 需求查询接口的异步 `RequirementClient`。尚未实现 LLM、LangGraph、Agent 工具或聊天接口。

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

测试与静态检查：

```bash
uv lock
uv run pytest
uv run ruff check .
uv run mypy app tests
```

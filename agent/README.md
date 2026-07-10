# Enterprise Support Agent Service

当前完成到阶段 6：提供 FastAPI 健康检查、异步 Java `RequirementClient`、只读查询工具，以及 DeepSeek + LangGraph 需求 Agent。尚未暴露聊天接口。

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

## DeepSeek 与 LangGraph

`RequirementAgent` 使用以下流程：

```text
用户消息 → DeepSeek 判断 → 可选查询工具 → DeepSeek 生成最终中文回答
```

- `RequirementAgentState` 使用 LangGraph 消息 reducer 保存上下文。
- 调用方将上一轮返回的 `history` 传入下一轮，即可实现基础多轮对话。
- 模型最多连续执行三轮工具调用，避免异常循环。
- 缺少 `DEEPSEEK_API_KEY` 时，健康检查仍可用；只有创建/调用 Agent 时返回配置错误。
- 自动化测试使用 Fake ChatModel，不调用真实 DeepSeek API。

当前默认模型仍为 `deepseek-chat`，可通过 `DEEPSEEK_MODEL` 替换。DeepSeek 官方已提示该别名将在 2026-07-24 弃用，部署时应按账号可用模型更新环境变量。

## 聊天接口

```http
POST /chat
Content-Type: application/json
```

请求体：

```json
{
  "userId": "user-001",
  "sessionId": "session-001",
  "message": "查询 XQ202607001 的当前进度"
}
```

`userId + sessionId` 在当前进程内唯一标识会话，最多保留最近 20 条消息；服务重启后会话会清空。当前实现不使用 Redis 或数据库。

```bash
curl -sS -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"userId":"user-001","sessionId":"session-001","message":"查询 XQ202607001"}'
```

缺少 `DEEPSEEK_API_KEY` 时，`/chat` 返回 `503 Service Unavailable` 和明确配置错误；`/health` 不受影响。

测试与静态检查：

```bash
uv lock
uv run pytest
uv run ruff check .
uv run mypy app tests
```

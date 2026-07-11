# Enterprise Support Agent Service

当前已完成阶段 7：提供 FastAPI 聊天接口、异步 Java `RequirementClient`、只读查询工具，以及 DeepSeek + LangGraph 需求 Agent。

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

## 本地端到端验证

最终效果需要同时启动 Java 后端和 Python Agent；默认 Java 后端使用内存数据，不需要 MySQL。

1. 在一个终端启动 Java 后端：

   ```powershell
   cd backend
   .\mvnw.cmd spring-boot:run
   ```

2. 在另一个终端启动 Agent，并设置 DeepSeek API Key：

   ```powershell
   cd agent
   $env:DEEPSEEK_API_KEY="你的 DeepSeek API Key"
   $env:BACKEND_BASE_URL="http://localhost:8080"
   uv run uvicorn app.main:app --reload --port 8000
   ```

3. 使用以下命令分别验证两个服务、Java 业务数据和最终聊天效果：

   ```powershell
   # Java 后端与 Python Agent 健康检查
   curl.exe -sS http://localhost:8080/health
   curl.exe -sS http://localhost:8000/health

   # Java 后端的示例需求数据
   curl.exe -sS http://localhost:8080/api/requirements/XQ202607002/progress

   # Agent → DeepSeek → Java 后端；单行命令可用于 PowerShell、Bash 和 CMD
   curl.exe -sS -X POST "http://localhost:8000/chat" -H "Content-Type: application/json; charset=utf-8" -d '{"userId":"demo-user","sessionId":"demo-session","message":"XQ202607002 \u76ee\u524d\u8fdb\u5c55\u600e\u4e48\u6837\uff1f"}'
   ```

Windows PowerShell 将中文直接传给 `curl.exe` 时，可能使用本地代码页编码，导致服务端无法按 UTF-8 解析请求体。上例使用 JSON Unicode 转义以确保兼容性。命令已保持单行，不依赖 PowerShell 的反引号、Bash 的反斜杠或 CMD 的脱字符续行。若希望直接输入中文，使用 PowerShell 的 `Invoke-RestMethod` 并显式传入 UTF-8 字节：

```powershell
$body = @{
  userId = "demo-user"
  sessionId = "demo-session"
  message = "XQ202607002 目前进展怎么样？"
} | ConvertTo-Json -Compress

$bytes = [System.Text.Encoding]::UTF8.GetBytes($body)

Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8000/chat" `
  -ContentType "application/json; charset=utf-8" `
  -Body $bytes
```

同一组 `userId` 与 `sessionId` 会保留最近 20 条对话上下文；服务重启后会清空。也可以访问 `http://localhost:8000/docs` 在 Swagger 页面调试 `/chat`。

测试与静态检查：

```bash
uv lock
uv run pytest
uv run ruff check .
uv run mypy app tests
```

# Enterprise Support Agent Service

Python Agent 服务，提供 FastAPI 聊天接口、异步 Java `RequirementClient`、只读查询工具，以及 DeepSeek + LangGraph 编排。本文只说明 Agent 的配置、运行、接口和验证；完整跨模块实现见 [当前调用链](../docs/current-flow.md)。

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

## 配置

配置全部来自环境变量：

```text
DEEPSEEK_API_KEY
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
BACKEND_BASE_URL=http://localhost:8080
BACKEND_TIMEOUT_SECONDS=10
SILICONFLOW_API_KEY
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
SILICONFLOW_EMBEDDING_MODEL=BAAI/bge-m3
CHROMA_PERSIST_DIRECTORY=data/chroma
CHROMA_COLLECTION_NAME=requirement_knowledge
```

Agent 只通过 Java API 获取业务数据，不直接访问数据库。Java 接口契约见 [需求查询 API](../docs/requirement-api.md)。缺少 `DEEPSEEK_API_KEY` 时，健康检查仍可用，`/chat` 返回配置错误。

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

成功响应包含 Agent 的中文回答。会话与错误处理的实现边界见 [当前调用链](../docs/current-flow.md)。

## SSE 流式聊天

`POST /chat/stream` 使用与 `/chat` 相同的 JSON 请求体，并以
`text/event-stream` 增量返回 DeepSeek 在生成过程中的最终回答。事件类型包括：

- `status`：Agent 正在处理请求。
- `tool`：安全、概括的工具开始或完成状态，不包含参数和原始结果。
- `message`：最终面向用户的回答 Token。
- `error`：响应流开始后的结构化错误，随后连接结束。
- `done`：本轮正常完成且会话历史已保存。

SSE 不会输出模型推理、系统提示词、工具参数或 LangGraph 原始事件。可用
`curl.exe -N` 禁用客户端缓冲并观察增量输出：

```powershell
curl.exe -N -X POST "http://localhost:8000/chat/stream" -H "Content-Type: application/json; charset=utf-8" -H "Accept: text/event-stream" -d '{"userId":"demo-user","sessionId":"stream-session","message":"XQ202607002 \u76ee\u524d\u8fdb\u5c55\u600e\u4e48\u6837？"}'
```

客户端中途断开时不会保存残缺的本轮历史。Swagger UI 不适合观察响应到达时序，
流式验收以 `curl.exe -N` 或支持读取流的客户端为准。

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

## Markdown 知识文档预览

业务知识文档位于仓库根目录的 `knowledge/`，当前只递归加载 UTF-8 Markdown
文件。可在 `agent/` 目录运行以下命令，人工查看文档及文本块数量、来源和正文：

```bash
uv run python -m app.rag.preview
```

如需临时预览其他目录，可设置 `KNOWLEDGE_ROOT` 环境变量。切分器优先使用
Markdown 标题和自然段边界，默认目标长度为 700 字符；超长段落优先在中文句末
继续切分，并保留约 100 字符重叠，兼顾业务章节完整性和边界上下文。

## 本地知识向量索引与检索预览

在 `.env` 或当前终端配置 `SILICONFLOW_API_KEY` 后，可将已经加载和切分的
Markdown 文档批量提交到硅基流动 Embedding API，并完整重建本地索引：

```bash
uv run python -m app.rag.indexer
```

索引命令会输出知识库目录、文档与 chunk 数量、Embedding 模型、collection、
持久化目录和实际写入数量。当前采用“构建前删除 collection，再完整写入”的策略，
因此重复执行不会累积重复 chunk，已经从知识库删除的文档也不会残留在索引中。

使用相同模型生成问题向量并预览最相关的三个文本块：

```bash
uv run python -m app.rag.search_preview "为什么需求既可以删除，也可以废弃？"
uv run python -m app.rag.search_preview "一级统筹是不是必须经过？" --top-k 5
```

输出中的 `distance` 是 Chroma 距离，数值越小表示越相关。Chroma 使用
`PersistentClient` 在 `agent/data/chroma/` 持久化，不需要启动独立服务；该目录已被
Git 忽略，不提交本地索引文件。相对的 `CHROMA_PERSIST_DIRECTORY` 始终以 `agent/`
为基准，不依赖启动命令所在目录。

索引记录了构建时的 Embedding 模型。更换 `SILICONFLOW_EMBEDDING_MODEL` 后必须重新
运行索引命令，否则检索会明确拒绝模型不一致的索引。当前阶段只返回相关文本块及
来源，不生成最终答案、不接入 Agent，也不增加 FastAPI 接口。

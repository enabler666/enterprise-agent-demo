# Enterprise Support Agent Service

Python 3.14 Agent 服务提供 FastAPI 普通聊天与 SSE 流式聊天，使用 DeepSeek + LangGraph 编排三个需求查询 Tool 和一个知识检索 Tool。需求数据只通过异步 `httpx` 调用 Java API；知识问答通过 SiliconFlow Embedding 查询本地 Chroma 索引。

## 安装与配置

```bash
uv sync
```

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
CHECKPOINT_DB_PATH=data/checkpoints.sqlite
```

Agent 不直接访问数据库。缺少 `DEEPSEEK_API_KEY` 时 `/health` 仍可用，普通 `/chat` 返回 HTTP 503，已开始的 SSE 流返回 `AGENT_UNAVAILABLE` 类型的 `error` 事件。

缺少 `SILICONFLOW_API_KEY` 时，三个需求查询 Tool 仍可工作；模型选择 `search_knowledge` 后会收到 `EMBEDDING_NOT_CONFIGURED` 安全错误。服务不会自动构建知识索引：索引不存在时返回 `KNOWLEDGE_INDEX_NOT_READY`，当前查询模型与索引模型不一致时返回 `EMBEDDING_MODEL_MISMATCH`。这些结果不会暴露密钥、底层堆栈或本地目录。

## 构建知识索引

业务知识位于仓库根目录 `knowledge/`。加载器递归读取 UTF-8 Markdown，切分器优先按 Markdown 标题和自然段切分，超长段落再按中文句末切分；默认目标长度约 700 字符、重叠约 100 字符。

配置 `SILICONFLOW_API_KEY` 后，在 `agent/` 目录完整重建索引：

```bash
uv run python -m app.rag.indexer
```

索引器会先删除同名 collection 再完整写入，因此重复构建不会累积重复 chunk，已删除文档也不会残留。Chroma 使用 `PersistentClient` 在本地持久化；相对的 `CHROMA_PERSIST_DIRECTORY` 始终以 `agent/` 为基准。

预览 Markdown 切分结果与向量检索结果：

```bash
uv run python -m app.rag.preview
uv run python -m app.rag.search_preview "一级统筹是不是必须经过？"
```

预览命令可以显示检索内部字段用于本地诊断；Agent 最终回答不会向用户输出向量、distance、chunk ID、片段序号或绝对路径。

## 启动服务

```bash
uv run uvicorn app.main:app --reload --port 8000
```

健康检查为 `GET http://localhost:8000/health`。需求查询还需启动 Java 后端；知识问答需要预先构建索引并保持查询与索引使用相同的 Embedding 模型。

## 普通聊天 `POST /chat`

请求体：

```json
{
  "userId": "user-001",
  "sessionId": "session-001",
  "message": "查询 XQ202607002 的当前进度"
}
```

业务查询：

```bash
curl -sS -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"userId":"user-001","sessionId":"session-001","message":"查询 XQ202607002 的当前进度"}'
```

知识问答：

```bash
curl -sS -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"userId":"user-001","sessionId":"knowledge-001","message":"一级统筹是不是必须经过？"}'
```

回答由模型根据实际召回内容生成，来源格式示例：

```text
一级统筹并非所有组织都必须经过，是否启用取决于组织当前配置。

参考来源：
- 《需求提报及流转相关说明》，需求提报及流转相关说明.md
```

找不到足够资料时，系统提示模型明确说明无法确认，不允许使用常识编造企业内部规则。

## SSE 流式聊天 `POST /chat/stream`

流式接口使用与 `/chat` 相同的请求体，并复用同一套 Agent、Tool 与会话流程：

```bash
curl -N -X POST "http://localhost:8000/chat/stream" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"userId":"user-001","sessionId":"knowledge-stream","message":"一级统筹是不是必须经过？"}'
```

知识问答的典型事件序列如下，具体 `message` 数量取决于模型输出分块：

```text
event: status
data: {"type":"status","status":"processing","message":"正在处理请求"}

event: tool
data: {"tool":"企业知识库检索","status":"started","message":"企业知识库检索正在执行","type":"tool"}

event: tool
data: {"tool":"企业知识库检索","status":"completed","message":"企业知识库检索执行完成","type":"tool"}

event: message
data: {"content":"一级统筹并非所有组织都必须经过……","type":"message"}

event: done
data: {"type":"done"}
```

五类公开事件：

| 事件 | 说明 |
| --- | --- |
| `status` | 请求已进入处理流程 |
| `tool` | 安全、概括的工具开始或完成状态 |
| `message` | 面向用户的最终回答文本增量 |
| `error` | 响应开始后的结构化错误，随后结束连接 |
| `done` | LangGraph 流正常完成 |

SSE 路由不理解也不转发 LangGraph 原始事件，不输出 reasoning、系统提示词、Tool 参数或原始 Tool 结果。Graph State 由 Checkpointer 在节点完成时保存，SSE 不维护第二套历史；Swagger UI 不适合观察响应时序，建议使用 `curl -N` 或支持流读取的客户端。

## 会话边界

`userId + sessionId` 经集中哈希生成固定长度的 LangGraph `thread_id`。普通与 SSE 接口只提交本轮消息，由 SQLite Checkpointer 恢复和保存线程 State，因此服务重启后可以继续会话。默认文件为 `agent/data/checkpoints.sqlite`；`CHECKPOINT_DB_PATH` 相对路径以 `agent/` 为基准。SQLite 适合本地单实例 Demo，不用于多实例共享。

## 当前 Tool 与 RAG 边界

| Tool | 数据来源 |
| --- | --- |
| `get_requirement_by_no` | Java 需求详情 API |
| `search_requirements` | Java 组合条件分页 API |
| `get_requirement_progress` | Java 需求进度 API |
| `search_knowledge` | Chroma Markdown 知识索引，固定 TopK 3 |

当前 RAG 只做向量 TopK 召回，不包含相似度阈值、Rerank、Hybrid Search、Query Rewrite 或自动评测。系统提示词暂不允许在同一轮组合结构化需求 Tool 与知识库 Tool。

## Windows 中文请求

PowerShell 直接将中文传给 `curl.exe` 时可能使用本地代码页。可以将中文写成 JSON Unicode 转义，或显式传入 UTF-8 字节：

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

## 测试与静态检查

Python 环境及验证由维护者执行：

```bash
uv lock
uv run pytest
uv run ruff check .
uv run mypy app tests
```

测试使用 Fake Model、Fake Retriever、`httpx.MockTransport` 和临时 Chroma，不访问真实 Java、DeepSeek 或 SiliconFlow 服务。完整跨模块说明见 [当前调用链](../docs/current-flow.md)，Java 接口契约见 [需求查询 API](../docs/requirement-api.md)。

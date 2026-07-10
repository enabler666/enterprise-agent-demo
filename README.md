# Enterprise Support Agent

企业需求与合同履约智能客服平台的 Monorepo。当前 Java 后端支持需求只读查询，以及内存/MySQL 两种数据模式。

## 目录

- `backend/`：JDK 25 + Spring Boot 4 Java 服务
- `agent/`：Python 3.14 + FastAPI 服务
- `docs/`：接口与架构文档
- `docker/`：MySQL 容器配置

## 环境要求

- JDK 25
- Python 3.14
- uv

## 验证

```bash
make test
```

分别启动：

```bash
cd backend && ./mvnw spring-boot:run
cd agent && uv run uvicorn app.main:app --reload --port 8000
```

健康检查分别位于 `GET http://localhost:8080/health` 和 `GET http://localhost:8000/health`。

## 最小联调

先分别启动 Java 后端和 Python Agent：

```powershell
cd backend
./mvnw.cmd spring-boot:run
```

```bash
cd agent
uv run uvicorn app.main:app --port 8000
```

调用聊天接口：

```bash
curl -sS -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"userId":"user-001","sessionId":"session-001","message":"查询 XQ202607001 的进度"}'
```

常见错误：

- `/chat` 返回 `503`：未配置 `DEEPSEEK_API_KEY`，请按 `.env.example` 设置环境变量。
- 查询工具返回后端不可用：确认 Java 后端运行在 `BACKEND_BASE_URL`（默认 `http://localhost:8080`）。
- MySQL 模式无法启动：先运行 `docker compose up -d mysql`，或使用默认内存模式。

## 文档

- [Java 后端说明](backend/README.md)
- [需求查询 API](docs/requirement-api.md)
- [开发执行计划](docs/development-plan.md)

# Enterprise Support Agent

企业需求与合同履约智能客服平台的 Monorepo。当前仅包含阶段 1 项目骨架和健康检查，不包含需求业务。

## 目录

- `backend/`：JDK 25 + Spring Boot 4 Java 服务
- `agent/`：Python 3.13 + FastAPI 服务
- `docs/`：架构与接口文档（后续阶段补充）
- `docker/`：容器配置（后续阶段补充）

## 环境要求

- JDK 25
- Python 3.13
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

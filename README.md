# Enterprise Support Agent

面向企业需求查询的智能客服 Agent Monorepo。当前产品范围仅包含需求的只读查询：Java 后端提供业务 API，Python Agent 通过 DeepSeek 与 LangGraph 将自然语言问题转换为受控查询。

## 仓库结构

| 目录 | 职责 |
| --- | --- |
| `backend/` | Java 25 + Spring Boot 业务后端，支持内存与 MySQL 两种数据模式 |
| `agent/` | Python 3.14 + FastAPI Agent 服务 |
| `docs/` | 接口契约、当前架构和开发阶段记录 |
| `docker/` | 本地 MySQL 配置 |

## 快速启动

启动 Java 后端（默认使用内存数据，无需 MySQL）：

```powershell
cd backend
./mvnw.cmd spring-boot:run
```

启动 Python Agent：

```powershell
cd agent
$env:DEEPSEEK_API_KEY="你的 DeepSeek API Key"
uv run uvicorn app.main:app --reload --port 8000
```

健康检查地址为 `http://localhost:8080/health` 和 `http://localhost:8000/health`。完整配置、调用示例和验证命令分别见两个子项目的 README。

## 文档入口

文档的用途与阅读顺序见 [docs/README.md](docs/README.md)。常用入口：

- [Java 后端运行与开发](backend/README.md)
- [Python Agent 运行与开发](agent/README.md)
- [需求查询 API 契约](docs/requirement-api.md)
- [当前调用链与架构边界](docs/current-flow.md)
- [开发路径与迭代记录](docs/development-history.md)

## 当前边界

仅支持读取需求详情、组合检索和当前进度。不包含需求写操作、合同、订单、认证、RAG、向量数据库、MCP、多 Agent 或自然语言 SQL。

# 仓库贡献指南

## 项目结构与模块职责

本仓库是企业智能客服 Agent 的 Monorepo：

- `backend/`：Java 25 + Spring Boot 业务后端。源码位于 `src/main/java/com/enabler`，测试位于 `src/test/java`。
- `agent/`：Python 3.14 + FastAPI Agent 服务。应用代码位于 `app/`，测试位于 `tests/`。
- `docs/`：接口约定、开发迭代记录和架构说明。
- `docker/`、`docker-compose.yml`：本地 MySQL 配置。

Java 按 `api`、`domain`、`repository`、`service`、`infrastructure` 分层。Python 的路由、Client、Schema、工具、提示词和 Agent 流程分别放入对应的 `app/` 子包。

## Agent 执行规则与范围

严格遵循 `docs/development-history.md`，每次只完成一个阶段。完成后汇报修改文件和验证结果，然后立即停止，等待维护者明确回复继续。

Codex 只负责代码和文档编辑，不执行 `git status`、暂存、提交、推送等 Git 操作。Git 操作由维护者完成。Python 环境及验证也由维护者执行；依赖变化时，应明确提示执行 `uv lock`、pytest、Ruff 和 mypy，不得声称未运行的检查已经通过。

`docs/development-history.md` 是唯一的开发路径与更新记录。维护者明确表示接下来开发某项能力时，Agent 必须在文件末尾自动追加下一个阶段，标记为“进行中”，然后再开始实现；不得提前追加尚未确认的阶段。实现完成后补充实际变化并标记为“待验收”；维护者确认验证结果后改为“已完成”。该文档不记录调试过程、文件清单或重复的接口细节。

Java 根包固定为 `com.enabler`，Python 固定为 3.14。当前产品范围仅限只读需求查询。除非后续已确认阶段明确要求，不得加入合同、订单、RAG、向量数据库、MCP、多 Agent、认证、工作流引擎、自然语言 SQL 或需求写操作。

## 构建、测试与开发命令

在 `backend/` 中执行：

```powershell
./mvnw.cmd clean verify
./mvnw.cmd spring-boot:run
$env:SPRING_PROFILES_ACTIVE="mysql"; ./mvnw.cmd spring-boot:run
```

在 `agent/` 中执行：

```bash
uv lock
uv run pytest
uv run ruff check .
uv run mypy app tests
uv run uvicorn app.main:app --reload --port 8000
```

测试 Java `mysql` Profile 前，在仓库根目录运行 `docker compose up -d mysql`。

## 编码风格与命名

Java 使用四空格缩进、构造器注入、`PascalCase` 类名，并优先用 record 表示不可变 DTO。Controller 不写业务逻辑，Service 只依赖 Repository 抽象。

Python 使用完整类型标注、四空格缩进、`snake_case` 模块和函数名、`PascalCase` Pydantic 模型。对 Python 特有语法、关键流程和扩展点添加简短中文注释，不注释显而易见的代码。禁止在模块导入阶段创建外部连接。

## 测试规范

Java 使用 JUnit 5、Mockito、Spring Test 和 Testcontainers。测试类使用 `*Test` 命名；分别验证默认 `local` 模式与数据库 Profile。Docker 不可用时，Testcontainers 测试可以跳过，但必须在汇报中说明。

Python 使用 pytest 和 `httpx.MockTransport`。单元测试不得调用真实 Java 或 DeepSeek 服务。Client 或工具变更应覆盖成功、无结果、参数校验和失败场景。

## 安全与配置

所有密钥和数据库凭据必须来自环境变量。禁止提交 `.env`、API Key 或真实密码；使用 `.env.example` 提供模板。Python 业务数据必须通过 Java API 获取，禁止直接访问数据库或生成 SQL。

## Commit 与 Pull Request

Commit message 使用 Conventional Commits 格式，但描述部分必须使用中文，例如：

```text
feat: 新增需求查询工具
chore: 初始化 Monorepo 项目骨架
fix: 修复需求分页查询条件
docs: 补充需求接口调用说明
```

后续由 Codex 建议或生成 commit message 时，也必须保持“英文类型前缀 + 中文描述”。每个提交只包含一个开发阶段或一个明确修复。

Pull Request 应说明所属阶段、主要改动、验证命令与结果、被跳过的 Docker/Python 测试，并链接相关文档或 Issue。

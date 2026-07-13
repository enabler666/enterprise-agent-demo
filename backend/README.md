# Enterprise Support Backend

企业需求智能客服的 Java 业务后端。本文只说明后端的运行、数据模式、测试和代码结构；接口细节以 [需求查询 API](../docs/requirement-api.md) 为准。

当前提供需求只读查询能力。默认使用内存数据运行，也可以通过 `mysql` Profile 切换到 MyBatis-Plus 和 MySQL。

## 技术环境

- JDK 25
- Spring Boot 4.1.0
- Maven 3.9.11（通过 Maven Wrapper 使用）
- MyBatis-Plus 3.5.16
- Flyway
- MySQL 8.4
- Testcontainers 2.0.5
- JUnit 5

编译目标明确设置为 Java 25。

## 快速启动

Windows PowerShell：

```powershell
cd backend
./mvnw.cmd spring-boot:run
```

Linux 或 macOS：

```bash
cd backend
./mvnw spring-boot:run
```

服务默认监听：

```text
http://localhost:8080
```

健康检查：

```bash
curl -sS "http://localhost:8080/health"
```

响应：

```json
{
  "status": "UP"
}
```

## 默认内存模式

默认 Profile 为 `local`：

- 使用 `InMemoryRequirementRepository`
- 初始化 12 条固定需求数据
- 不创建数据源
- 不连接 MySQL
- 不依赖外部服务即可启动

Repository 关系：

```text
RequirementService
       │
       ▼
RequirementRepository
       │
       ▼
InMemoryRequirementRepository
```

Service 只依赖 `RequirementRepository` 抽象，不包含内存和数据库实现之间的判断逻辑。

## MySQL 模式

MySQL 模式使用：

- `MyBatisRequirementRepository`
- MyBatis-Plus Mapper 和数据库分页
- Flyway 初始化表结构及 12 条演示数据
- MySQL 环境变量配置

从仓库根目录启动 MySQL：

```bash
docker compose up -d mysql
```

默认开发配置为：

```text
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=enterprise_support
MYSQL_USERNAME=enterprise_support
MYSQL_PASSWORD=change-me
```

可以复制根目录 `.env.example` 为 `.env` 并修改本地配置。不要提交包含真实密码的 `.env`。

启动 MySQL Profile：

Windows PowerShell：

```powershell
$env:SPRING_PROFILES_ACTIVE = "mysql"
./mvnw.cmd spring-boot:run
```

Linux 或 macOS：

```bash
SPRING_PROFILES_ACTIVE=mysql ./mvnw spring-boot:run
```

也可以显式传递 Profile：

```text
./mvnw spring-boot:run -Dspring-boot.run.profiles=mysql
```

首次启动时 Flyway 会自动执行：

```text
src/main/resources/db/migration/V1__create_requirements.sql
```

`local` 与 `mysql` Profile 通过 Spring Bean/Profile 切换 Repository，Controller 和 Service 不需要感知具体数据来源。

## 需求查询接口入口

当前提供三个只读接口：

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `GET` | `/api/requirements/{requirementNo}` | 根据需求编号精确查询 |
| `GET` | `/api/requirements` | 组合条件及分页查询 |
| `GET` | `/api/requirements/{requirementNo}/progress` | 查询当前进度 |

完整参数、响应格式、错误码和 curl 示例统一维护在：

- [需求查询 API](../docs/requirement-api.md)

业务接口支持通过 `X-Trace-Id` 请求头传入链路标识；统一响应、校验规则和错误处理约定也以该 API 文档为准。

## 编译和测试

Windows：

```powershell
./mvnw.cmd clean verify
```

Linux 或 macOS：

```bash
./mvnw clean verify
```

当前测试覆盖：

- 默认 `local` Profile 的 Spring 上下文启动
- 内存 Repository 精确查询、组合过滤、时间范围和分页
- Service DTO 映射、进度查询和未找到异常
- 三个 HTTP 接口
- 统一成功和错误响应
- traceId 透传
- 分页及状态参数校验
- MySQL Profile 的 Repository 切换
- Flyway 表结构和演示数据初始化
- MyBatis-Plus 数据库过滤与分页

MySQL 集成测试使用 Testcontainers。如果本机没有可用 Docker，相关测试会标记为跳过，其他测试仍会执行。要完整运行集成测试，请先启动 Docker Desktop 或兼容的 Docker Engine。

## 代码结构

```text
src/main/java/com/enabler/
├── EnterpriseSupportApplication.java
├── health/
│   └── HealthController.java
├── common/
│   ├── api/
│   ├── exception/
│   └── trace/
└── requirement/
    ├── api/
    ├── domain/
    ├── exception/
    ├── infrastructure/mybatis/
    ├── repository/
    └── service/
```

主要职责：

- `api`：Controller、请求对象和响应 DTO
- `domain`：领域模型、查询条件和状态枚举
- `repository`：数据访问抽象及内存实现
- `infrastructure/mybatis`：MyBatis-Plus Entity、Mapper 和分页配置
- `repository`：Repository 抽象、内存实现和 MySQL 实现
- `service`：查询业务编排和 DTO 转换
- `common`：统一响应、异常处理和 traceId

## 数据库文件

```text
backend/src/main/resources/
├── application-local.yml
├── application-mysql.yml
└── db/migration/
    └── V1__create_requirements.sql

docker/mysql/conf.d/
└── charset.cnf
```

## 当前边界

当前不包含：

- 创建、修改、审批或删除需求
- 合同、订单和履约模块
- 登录认证
- RAG、MCP 或自然语言 SQL

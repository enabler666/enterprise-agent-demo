# Enterprise Support Backend

企业需求与合同履约智能客服平台的 Java 业务后端。

当前完成到阶段 2，只提供需求查询能力。默认使用内存数据运行，不需要安装或启动 MySQL。

## 技术环境

- JDK 25
- Spring Boot 4.1.0
- Maven 3.9.11（通过 Maven Wrapper 使用）
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

## 运行模式

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

`mysql` Profile 及 MyBatis-Plus Repository 将在阶段 3 实现，当前不要使用：

```text
--spring.profiles.active=mysql
```

## 需求查询接口

当前提供三个只读接口：

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `GET` | `/api/requirements/{requirementNo}` | 根据需求编号精确查询 |
| `GET` | `/api/requirements` | 组合条件及分页查询 |
| `GET` | `/api/requirements/{requirementNo}/progress` | 查询当前进度 |

完整参数、响应格式、错误码和 curl 示例见：

- [需求查询 API](../docs/requirement-api.md)

简单示例：

```bash
curl -sS \
  -H "X-Trace-Id: backend-readme-demo" \
  "http://localhost:8080/api/requirements/XQ202607001"
```

组合查询：

```bash
curl -sS --get \
  "http://localhost:8080/api/requirements" \
  --data-urlencode "title=服务器" \
  --data-urlencode "status=EXECUTING" \
  --data-urlencode "page=0" \
  --data-urlencode "size=10"
```

## 统一响应与 traceId

业务接口使用统一响应结构：

```json
{
  "success": true,
  "code": "OK",
  "message": "查询成功",
  "data": {},
  "traceId": "backend-readme-demo"
}
```

可以通过 `X-Trace-Id` 请求头传入 traceId。未提供时服务端自动生成。服务端会将 traceId：

- 放入响应体
- 写入 `X-Trace-Id` 响应头
- 放入日志上下文

业务异常不会向调用方返回堆栈；未预期异常的堆栈只记录在服务端日志中。

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
    ├── repository/
    └── service/
```

主要职责：

- `api`：Controller、请求对象和响应 DTO
- `domain`：领域模型、查询条件和状态枚举
- `repository`：数据访问抽象及内存实现
- `service`：查询业务编排和 DTO 转换
- `common`：统一响应、异常处理和 traceId

## 当前数据范围

内存数据包含 12 条需求，覆盖：

- 信息技术部、行政部、财务部、研发部等多个部门
- 多个申请人和需求类型
- 草稿、审批中、已批准、驳回、执行中、已完成和已取消状态
- 多条服务器相关需求
- 2026 年 5 月至 7 月的不同创建时间

示例需求编号：

```text
XQ202607001
XQ202607002
XQ202606001
XQ202605001
```

## 当前边界

当前不包含：

- MyBatis-Plus 和 MySQL 实现
- Flyway 数据库迁移
- 创建、修改、审批或删除需求
- 合同、订单和履约模块
- 登录认证
- Python Agent 调用
- RAG、MCP 或自然语言 SQL

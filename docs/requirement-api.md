# 需求查询 API

本文是 Java 需求查询接口的权威契约。模块 README 只提供入口，不重复维护参数、响应和错误码。

Java 后端默认地址：`http://localhost:8080`。

当前接口为只读接口，默认使用 `local` Profile 和内存数据，不需要启动 MySQL。

## 通用约定

所有业务接口返回统一结构：

```json
{
  "success": true,
  "code": "OK",
  "message": "查询成功",
  "data": {},
  "traceId": "trace-demo-001"
}
```

客户端可以通过 `X-Trace-Id` 请求头传入链路标识。未传入时，服务端会自动生成。响应体的 `traceId` 和响应头 `X-Trace-Id` 使用同一个值。

## 启动后端

Windows：

```powershell
cd backend
./mvnw.cmd spring-boot:run
```

Linux 或 macOS：

```bash
cd backend
./mvnw spring-boot:run
```

## 1. 根据需求编号查询

```http
GET /api/requirements/{requirementNo}
```

`requirementNo` 使用精确匹配。

### curl 示例

```bash
curl -sS \
  -H "X-Trace-Id: trace-demo-001" \
  "http://localhost:8080/api/requirements/XQ202607001"
```

### 成功响应

```json
{
  "success": true,
  "code": "OK",
  "message": "查询成功",
  "data": {
    "id": 1,
    "requirementNo": "XQ202607001",
    "title": "新增生产服务器",
    "description": "采购两台生产服务器",
    "applicantId": "U001",
    "applicantName": "张伟",
    "department": "信息技术部",
    "type": "设备采购",
    "status": "PENDING_APPROVAL",
    "currentNode": "部门负责人审批",
    "expectedCompletionDate": "2026-08-15",
    "createdAt": "2026-07-01T09:00:00+08:00",
    "updatedAt": "2026-07-03T09:00:00+08:00"
  },
  "traceId": "trace-demo-001"
}
```

### 未找到响应

HTTP 状态码：`404 Not Found`

```json
{
  "success": false,
  "code": "REQUIREMENT_NOT_FOUND",
  "message": "未找到需求 XQ-NOT-FOUND",
  "data": null,
  "traceId": "trace-demo-001"
}
```

## 2. 组合条件查询

```http
GET /api/requirements
```

所有查询条件均可选。

| 参数 | 类型 | 默认值 | 查询规则 |
| --- | --- | --- | --- |
| `requirementNo` | string | - | 精确匹配 |
| `title` | string | - | 忽略大小写的包含匹配 |
| `applicantId` | string | - | 精确匹配 |
| `applicantName` | string | - | 精确匹配 |
| `department` | string | - | 精确匹配 |
| `status` | enum | - | 精确匹配需求状态 |
| `createdFrom` | ISO 8601 datetime | - | 创建时间下界，包含边界 |
| `createdTo` | ISO 8601 datetime | - | 创建时间上界，包含边界 |
| `page` | integer | `0` | 从 0 开始的页码 |
| `size` | integer | `20` | 每页 1–100 条 |

可用状态：

```text
DRAFT
PENDING_APPROVAL
APPROVED
REJECTED
EXECUTING
COMPLETED
CANCELLED
```

### 按标题和状态查询

```bash
curl -sS --get \
  "http://localhost:8080/api/requirements" \
  --data-urlencode "title=服务器" \
  --data-urlencode "status=EXECUTING" \
  --data-urlencode "page=0" \
  --data-urlencode "size=10"
```

### 按部门和创建时间查询

```bash
curl -sS --get \
  "http://localhost:8080/api/requirements" \
  --data-urlencode "department=信息技术部" \
  --data-urlencode "createdFrom=2026-07-01T00:00:00+08:00" \
  --data-urlencode "createdTo=2026-07-31T23:59:59+08:00"
```

### 分页响应

```json
{
  "success": true,
  "code": "OK",
  "message": "查询成功",
  "data": {
    "items": [],
    "total": 0,
    "page": 0,
    "size": 20,
    "totalPages": 0
  },
  "traceId": "9a4642ca-aac7-4ee8-a737-469641acdc85"
}
```

查询无结果时返回成功响应，`items` 为空数组，`total` 为 `0`。

## 3. 查询当前进度

```http
GET /api/requirements/{requirementNo}/progress
```

当前版本只返回需求当前节点，不包含审批历史。

### curl 示例

```bash
curl -sS \
  "http://localhost:8080/api/requirements/XQ202607002/progress"
```

### 成功响应

```json
{
  "success": true,
  "code": "OK",
  "message": "查询成功",
  "data": {
    "requirementNo": "XQ202607002",
    "title": "服务器扩容申请",
    "status": "EXECUTING",
    "currentNode": "执行中",
    "createdAt": "2026-07-02T10:30:00+08:00",
    "updatedAt": "2026-07-04T10:30:00+08:00",
    "expectedCompletionDate": "2026-07-31"
  },
  "traceId": "9a4642ca-aac7-4ee8-a737-469641acdc85"
}
```

## 参数错误

非法状态、分页越界、时间格式错误或 `createdFrom` 晚于 `createdTo` 时返回 `400 Bad Request`：

```json
{
  "success": false,
  "code": "INVALID_ARGUMENT",
  "message": "请求参数不合法",
  "data": null,
  "traceId": "9a4642ca-aac7-4ee8-a737-469641acdc85"
}
```

示例：

```bash
curl -sS --get \
  "http://localhost:8080/api/requirements" \
  --data-urlencode "status=UNKNOWN"
```

## 当前业务错误码

| HTTP 状态码 | code | 含义 |
| --- | --- | --- |
| `200` | `OK` | 查询成功，组合查询可能返回空列表 |
| `400` | `INVALID_ARGUMENT` | 查询参数格式或取值不合法 |
| `404` | `REQUIREMENT_NOT_FOUND` | 指定需求编号不存在 |
| `500` | `INTERNAL_ERROR` | 未预期的服务端错误 |

"""Java 需求查询 API 的异步 HTTP Client。"""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import ValidationError

from app.core.config import Settings
from app.core.exceptions import BackendBusinessError, BackendProtocolError, BackendTransportError
from app.schemas.requirement import (
    ApiResponse,
    PageResult,
    Requirement,
    RequirementProgress,
    RequirementQuery,
)


class RequirementClient:
    """可替换的 Java 后端 Client。

构造器允许注入 ``httpx.AsyncClient``：生产环境默认自行创建，测试则注入
``MockTransport``，因此测试不会产生真实网络请求。
"""

    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = str(settings.backend_base_url).rstrip("/")
        self._client = client or httpx.AsyncClient(timeout=settings.backend_timeout_seconds)
        self._owns_client = client is None

    async def close(self) -> None:
        """仅关闭由本类创建的 Client，避免误关闭调用方注入的共享 Client。"""
        if self._owns_client:
            await self._client.aclose()

    async def get_requirement_by_no(
        self, requirement_no: str, trace_id: str | None = None
    ) -> Requirement:
        payload = await self._get(f"/api/requirements/{requirement_no}", trace_id=trace_id)
        return self._validate_data(payload, Requirement)

    async def search_requirements(
        self, query: RequirementQuery, trace_id: str | None = None
    ) -> PageResult[Requirement]:
        payload = await self._get(
            "/api/requirements", params=query.as_query_params(), trace_id=trace_id
        )
        return self._validate_data(payload, PageResult[Requirement])

    async def get_requirement_progress(
        self, requirement_no: str, trace_id: str | None = None
    ) -> RequirementProgress:
        payload = await self._get(
            f"/api/requirements/{requirement_no}/progress", trace_id=trace_id
        )
        return self._validate_data(payload, RequirementProgress)

    async def _get(
        self,
        path: str,
        params: dict[str, str | int] | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        headers = {"X-Trace-Id": trace_id} if trace_id else None
        # ``await`` 表示等待异步 I/O 完成，不会像同步网络调用那样阻塞整个事件循环。
        # Client 只传递调用方已有的追踪号；未提供时交由 Java TraceIdFilter 生成并回写响应。
        try:
            response = await self._client.get(
                f"{self._base_url}{path}", params=params, headers=headers
            )
        except httpx.RequestError as error:
            raise BackendTransportError("无法连接需求查询服务") from error

        try:
            raw_payload: dict[str, Any] = response.json()
        except ValueError as error:
            raise BackendProtocolError("需求查询服务返回了非 JSON 响应") from error

        if not response.is_success:
            # 即使 HTTP 是 4xx/5xx，也要求后端返回 ApiResponse，才能保留业务码和 traceId。
            self._raise_backend_error(raw_payload, response.status_code)

        try:
            envelope = ApiResponse[Any].model_validate(raw_payload)
        except ValidationError as error:
            raise BackendProtocolError("需求查询服务响应格式不合法") from error

        if not envelope.success:
            raise BackendBusinessError(
                envelope.code, envelope.message, envelope.trace_id, response.status_code
            )
        if envelope.data is None:
            raise BackendProtocolError("需求查询服务成功响应缺少 data")
        return raw_payload

    def _raise_backend_error(self, payload: dict[str, Any], status_code: int) -> None:
        try:
            envelope = ApiResponse[Any].model_validate(payload)
        except ValidationError as error:
            raise BackendProtocolError("需求查询服务错误响应格式不合法") from error
        raise BackendBusinessError(envelope.code, envelope.message, envelope.trace_id, status_code)

    def _validate_data(self, payload: dict[str, Any], model: type[Any]) -> Any:
        """二次校验 data 字段，防止后端响应缺字段后流入 Agent。"""
        try:
            return model.model_validate(payload["data"])
        except (KeyError, ValidationError) as error:
            raise BackendProtocolError("需求查询服务 data 格式不合法") from error

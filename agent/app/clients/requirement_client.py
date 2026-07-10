"""Async HTTP client for the Java requirement query API."""

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
    """A replaceable, read-only client for the Java backend requirement endpoints."""

    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = str(settings.backend_base_url).rstrip("/")
        self._client = client or httpx.AsyncClient(timeout=settings.backend_timeout_seconds)
        self._owns_client = client is None

    async def close(self) -> None:
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
        try:
            return model.model_validate(payload["data"])
        except (KeyError, ValidationError) as error:
            raise BackendProtocolError("需求查询服务 data 格式不合法") from error

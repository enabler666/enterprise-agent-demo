import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
import pytest

from app.clients.requirement_client import RequirementClient
from app.core.config import Settings
from app.core.exceptions import BackendBusinessError, BackendTransportError
from app.schemas.requirement import RequirementQuery, RequirementStatus


def test_get_requirement_by_no_maps_java_response_and_trace_id() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/requirements/XQ202607001"
        assert request.headers["X-Trace-Id"] == "trace-001"
        return httpx.Response(200, json=success_response(requirement_data()))

    client = client_with_handler(handler)

    result = asyncio.run(client.get_requirement_by_no("XQ202607001", trace_id="trace-001"))

    assert result.requirement_no == "XQ202607001"
    assert result.status is RequirementStatus.PENDING_APPROVAL


def test_search_sends_camel_case_query_parameters() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/requirements"
        assert dict(request.url.params) == {
            "applicantName": "张伟",
            "createdFrom": "2026-07-01T00:00:00+08:00",
            "page": "0",
            "size": "10",
        }
        return httpx.Response(
            200,
            json=success_response(
                {
                    "items": [requirement_data()],
                    "total": 1,
                    "page": 0,
                    "size": 10,
                    "totalPages": 1,
                }
            ),
        )

    client = client_with_handler(handler)
    query = RequirementQuery(
        applicant_name="张伟", created_from="2026-07-01T00:00:00+08:00", size=10
    )

    result = asyncio.run(client.search_requirements(query))

    assert result.total == 1
    assert result.items[0].requirement_no == "XQ202607001"


def test_maps_documented_backend_business_error() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            json={
                "success": False,
                "code": "REQUIREMENT_NOT_FOUND",
                "message": "未找到需求 XQ-NOT-FOUND",
                "data": None,
                "traceId": "trace-404",
            },
        )

    client = client_with_handler(handler)

    with pytest.raises(BackendBusinessError) as error:
        asyncio.run(client.get_requirement_by_no("XQ-NOT-FOUND"))

    assert error.value.code == "REQUIREMENT_NOT_FOUND"
    assert error.value.trace_id == "trace-404"
    assert error.value.status_code == 404


def test_maps_transport_failure() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    client = client_with_handler(handler)

    with pytest.raises(BackendTransportError):
        asyncio.run(client.get_requirement_progress("XQ202607001"))


def test_settings_reads_environment_without_exposing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-secret")
    monkeypatch.setenv("BACKEND_BASE_URL", "http://backend.example:8080")

    settings = Settings.from_environment()

    assert settings.deepseek_api_key is not None
    assert settings.deepseek_api_key.get_secret_value() == "test-secret"
    assert str(settings.backend_base_url) == "http://backend.example:8080/"
    assert "test-secret" not in repr(settings)


MockHandler = Callable[[httpx.Request], httpx.Response | Awaitable[httpx.Response]]


def client_with_handler(handler: MockHandler) -> RequirementClient:
    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(transport=transport)
    return RequirementClient(Settings(), client=http_client)


def success_response(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "success": True,
        "code": "OK",
        "message": "查询成功",
        "data": data,
        "traceId": "trace-success",
    }


def requirement_data() -> dict[str, Any]:
    return {
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
        "updatedAt": "2026-07-03T09:00:00+08:00",
    }

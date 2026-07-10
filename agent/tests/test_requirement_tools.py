import asyncio
from datetime import date, datetime, timezone

from app.core.exceptions import BackendBusinessError, BackendTransportError
from app.schemas.requirement import (
    PageResult,
    Requirement,
    RequirementProgress,
    RequirementQuery,
    RequirementStatus,
)
from app.tools.requirement_tools import RequirementTools
from app.tools.result import ToolExecutionStatus


class FakeRequirementBackend:
    def __init__(self) -> None:
        self.requirement: Requirement | Exception = sample_requirement()
        self.progress: RequirementProgress | Exception = sample_progress()
        self.search_result: PageResult[Requirement] | Exception = PageResult(
            items=[sample_requirement()], total=1, page=0, size=20, total_pages=1
        )

    async def get_requirement_by_no(
        self, requirement_no: str, trace_id: str | None = None
    ) -> Requirement:
        if isinstance(self.requirement, Exception):
            raise self.requirement
        return self.requirement

    async def search_requirements(
        self, query: RequirementQuery, trace_id: str | None = None
    ) -> PageResult[Requirement]:
        if isinstance(self.search_result, Exception):
            raise self.search_result
        return self.search_result

    async def get_requirement_progress(
        self, requirement_no: str, trace_id: str | None = None
    ) -> RequirementProgress:
        if isinstance(self.progress, Exception):
            raise self.progress
        return self.progress


def test_get_requirement_by_no_returns_success() -> None:
    tools = RequirementTools(FakeRequirementBackend())

    result = asyncio.run(tools.get_requirement_by_no({"requirement_no": " XQ202607001 "}))

    assert result.status is ToolExecutionStatus.SUCCESS
    assert result.code == "OK"
    assert result.data is not None
    assert result.data.requirement_no == "XQ202607001"


def test_search_returns_no_result_for_empty_page() -> None:
    backend = FakeRequirementBackend()
    backend.search_result = PageResult(items=[], total=0, page=0, size=20, total_pages=0)
    tools = RequirementTools(backend)

    result = asyncio.run(tools.search_requirements({"department": "采购部"}))

    assert result.status is ToolExecutionStatus.NO_RESULT
    assert result.code == "NO_RESULT"
    assert result.data is None


def test_invalid_tool_arguments_return_error_result() -> None:
    tools = RequirementTools(FakeRequirementBackend())

    result = asyncio.run(tools.get_requirement_progress({"requirement_no": "invalid value!"}))

    assert result.status is ToolExecutionStatus.ERROR
    assert result.code == "INVALID_ARGUMENT"
    assert result.data is None


def test_not_found_backend_error_becomes_no_result() -> None:
    backend = FakeRequirementBackend()
    backend.requirement = BackendBusinessError(
        "REQUIREMENT_NOT_FOUND", "未找到需求 XQ202607999", "trace-404", 404
    )
    tools = RequirementTools(backend)

    result = asyncio.run(tools.get_requirement_by_no({"requirement_no": "XQ202607999"}))

    assert result.status is ToolExecutionStatus.NO_RESULT
    assert result.code == "REQUIREMENT_NOT_FOUND"
    assert result.trace_id == "trace-404"


def test_backend_transport_failure_does_not_expose_internal_details() -> None:
    backend = FakeRequirementBackend()
    backend.progress = BackendTransportError("connection refused")
    tools = RequirementTools(backend)

    result = asyncio.run(tools.get_requirement_progress({"requirement_no": "XQ202607001"}))

    assert result.status is ToolExecutionStatus.ERROR
    assert result.code == "BACKEND_UNAVAILABLE"
    assert result.message == "需求查询服务暂时不可用"


def sample_requirement() -> Requirement:
    now = datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc)
    return Requirement(
        id=1,
        requirement_no="XQ202607001",
        title="新增生产服务器",
        description="采购两台生产服务器",
        applicant_id="U001",
        applicant_name="张伟",
        department="信息技术部",
        type="设备采购",
        status=RequirementStatus.PENDING_APPROVAL,
        current_node="部门负责人审批",
        expected_completion_date=date(2026, 8, 15),
        created_at=now,
        updated_at=now,
    )


def sample_progress() -> RequirementProgress:
    requirement = sample_requirement()
    return RequirementProgress(
        requirement_no=requirement.requirement_no,
        title=requirement.title,
        status=requirement.status,
        current_node=requirement.current_node,
        created_at=requirement.created_at,
        updated_at=requirement.updated_at,
        expected_completion_date=requirement.expected_completion_date,
    )

"""Read-only requirement query tools for the later Agent workflow."""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field, ValidationError, field_validator

from app.core.exceptions import (
    BackendBusinessError,
    BackendProtocolError,
    BackendTransportError,
)
from app.schemas.requirement import PageResult, Requirement, RequirementProgress, RequirementQuery
from app.tools.result import ToolExecutionResult


class RequirementBackend(Protocol):
    async def get_requirement_by_no(
        self, requirement_no: str, trace_id: str | None = None
    ) -> Requirement: ...

    async def search_requirements(
        self, query: RequirementQuery, trace_id: str | None = None
    ) -> PageResult[Requirement]: ...

    async def get_requirement_progress(
        self, requirement_no: str, trace_id: str | None = None
    ) -> RequirementProgress: ...


class RequirementNoInput(BaseModel):
    requirement_no: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")

    @field_validator("requirement_no", mode="before")
    @classmethod
    def strip_requirement_no(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class SearchRequirementsInput(RequirementQuery):
    """Input schema for the combined requirement query tool."""


class RequirementTools:
    """Tools that only read business data through the Java backend client."""

    def __init__(self, backend: RequirementBackend) -> None:
        self._backend = backend

    async def get_requirement_by_no(
        self, payload: object, trace_id: str | None = None
    ) -> ToolExecutionResult[Requirement]:
        try:
            input_data = RequirementNoInput.model_validate(payload)
        except ValidationError as error:
            return ToolExecutionResult.invalid_arguments(error)

        try:
            requirement = await self._backend.get_requirement_by_no(
                input_data.requirement_no, trace_id=trace_id
            )
        except BackendBusinessError as error:
            return self._map_business_error(error)
        except BackendTransportError:
            return ToolExecutionResult.failure(
                code="BACKEND_UNAVAILABLE", message="需求查询服务暂时不可用"
            )
        except BackendProtocolError:
            return ToolExecutionResult.failure(
                code="BACKEND_PROTOCOL_ERROR", message="需求查询服务响应异常"
            )
        return ToolExecutionResult.success(requirement)

    async def search_requirements(
        self, payload: object, trace_id: str | None = None
    ) -> ToolExecutionResult[list[Requirement]]:
        try:
            input_data = SearchRequirementsInput.model_validate(payload)
        except ValidationError as error:
            return ToolExecutionResult.invalid_arguments(error)

        try:
            page = await self._backend.search_requirements(input_data, trace_id=trace_id)
        except BackendBusinessError as error:
            return self._map_business_error(error)
        except BackendTransportError:
            return ToolExecutionResult.failure(
                code="BACKEND_UNAVAILABLE", message="需求查询服务暂时不可用"
            )
        except BackendProtocolError:
            return ToolExecutionResult.failure(
                code="BACKEND_PROTOCOL_ERROR", message="需求查询服务响应异常"
            )

        if page.total == 0:
            return ToolExecutionResult.no_result(message="未找到符合条件的需求")
        return ToolExecutionResult.success(page.items)

    async def get_requirement_progress(
        self, payload: object, trace_id: str | None = None
    ) -> ToolExecutionResult[RequirementProgress]:
        try:
            input_data = RequirementNoInput.model_validate(payload)
        except ValidationError as error:
            return ToolExecutionResult.invalid_arguments(error)

        try:
            progress = await self._backend.get_requirement_progress(
                input_data.requirement_no, trace_id=trace_id
            )
        except BackendBusinessError as error:
            return self._map_business_error(error)
        except BackendTransportError:
            return ToolExecutionResult.failure(
                code="BACKEND_UNAVAILABLE", message="需求查询服务暂时不可用"
            )
        except BackendProtocolError:
            return ToolExecutionResult.failure(
                code="BACKEND_PROTOCOL_ERROR", message="需求查询服务响应异常"
            )
        return ToolExecutionResult.success(progress)

    def _map_business_error(self, error: BackendBusinessError) -> ToolExecutionResult[Any]:
        if error.code == "REQUIREMENT_NOT_FOUND":
            return ToolExecutionResult.no_result(
                message="未找到指定需求", code=error.code, trace_id=error.trace_id
            )
        return ToolExecutionResult.failure(
            code=error.code, message="需求查询服务返回业务错误", trace_id=error.trace_id
        )

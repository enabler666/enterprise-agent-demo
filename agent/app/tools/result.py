"""Stable result contract shared by all Agent tools."""

from __future__ import annotations

from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, ValidationError


class ToolExecutionStatus(StrEnum):
    SUCCESS = "SUCCESS"
    NO_RESULT = "NO_RESULT"
    ERROR = "ERROR"


T = TypeVar("T")


class ToolExecutionResult(BaseModel, Generic[T]):
    status: ToolExecutionStatus
    data: T | None = None
    code: str
    message: str
    trace_id: str | None = None

    @classmethod
    def success(cls, data: T, message: str = "查询成功") -> ToolExecutionResult[T]:
        return cls(status=ToolExecutionStatus.SUCCESS, data=data, code="OK", message=message)

    @classmethod
    def no_result(
        cls,
        message: str,
        code: str = "NO_RESULT",
        trace_id: str | None = None,
    ) -> ToolExecutionResult[T]:
        return cls(
            status=ToolExecutionStatus.NO_RESULT,
            data=None,
            code=code,
            message=message,
            trace_id=trace_id,
        )

    @classmethod
    def failure(
        cls, code: str, message: str, trace_id: str | None = None
    ) -> ToolExecutionResult[T]:
        return cls(
            status=ToolExecutionStatus.ERROR,
            data=None,
            code=code,
            message=message,
            trace_id=trace_id,
        )

    @classmethod
    def invalid_arguments(cls, error: ValidationError) -> ToolExecutionResult[T]:
        return cls.failure(code="INVALID_ARGUMENT", message="查询参数不合法")

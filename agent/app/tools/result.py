"""所有 Agent 工具共用的稳定结果契约。"""

from __future__ import annotations

from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, ValidationError


class ToolExecutionStatus(StrEnum):
    """工具状态与 HTTP 状态分离，方便后续 LangGraph 做分支判断。"""
    SUCCESS = "SUCCESS"
    NO_RESULT = "NO_RESULT"
    ERROR = "ERROR"


T = TypeVar("T")


class ToolExecutionResult(BaseModel, Generic[T]):
    """工具执行结果。

``data`` 只在成功时存在；泛型 ``T`` 保留具体数据类型，避免工具使用方退化为无类型字典。
"""
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

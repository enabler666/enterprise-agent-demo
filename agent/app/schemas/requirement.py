"""Java 后端 Client 与后续 Agent 工具共用的数据契约。"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel


class JavaApiModel(BaseModel):
    """Java JSON 与 Python 命名风格之间的适配基类。

Python 推荐 ``snake_case``，Java API 返回 ``camelCase``；Pydantic 的 alias 配置负责
双向转换，业务代码始终使用 Python 字段名。
"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class RequirementStatus(StrEnum):
    """``StrEnum`` 同时是字符串和枚举，序列化为 Java API 所需的状态文本。"""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Requirement(JavaApiModel):
    id: int
    requirement_no: str
    title: str
    description: str
    applicant_id: str
    applicant_name: str
    department: str
    type: str
    status: RequirementStatus
    current_node: str
    expected_completion_date: date
    created_at: datetime
    updated_at: datetime


class RequirementProgress(JavaApiModel):
    requirement_no: str
    title: str
    status: RequirementStatus
    current_node: str
    created_at: datetime
    updated_at: datetime
    expected_completion_date: date


class RequirementQuery(JavaApiModel):
    """组合查询输入；字段校验在构造对象时完成。"""
    requirement_no: str | None = None
    title: str | None = None
    applicant_id: str | None = None
    applicant_name: str | None = None
    department: str | None = None
    status: RequirementStatus | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None
    page: int = Field(default=0, ge=0)
    size: int = Field(default=20, ge=1, le=100)

    @field_validator(
        "requirement_no", "title", "applicant_id", "applicant_name", "department", mode="before"
    )
    @classmethod
    def blank_string_to_none(cls, value: object) -> object:
        return None if isinstance(value, str) and not value.strip() else value

    def as_query_params(self) -> dict[str, str | int]:
        """转为 httpx 查询参数，``by_alias`` 输出 Java 使用的 camelCase 名称。"""
        values = self.model_dump(exclude_none=True, mode="json", by_alias=True)
        return {key: value for key, value in values.items() if value != ""}

    @model_validator(mode="after")
    def validate_created_range(self) -> RequirementQuery:
        """``model_validator`` 在单字段转换后校验两个时间字段的关系。"""
        if self.created_from and self.created_to and self.created_from > self.created_to:
            raise ValueError("created_from must not be after created_to")
        return self


T = TypeVar("T")


class PageResult(JavaApiModel, Generic[T]):
    """``Generic[T]`` 表示分页项类型可复用，如 ``PageResult[Requirement]``。"""
    items: list[T]
    total: int = Field(ge=0)
    page: int = Field(ge=0)
    size: int = Field(ge=1)
    total_pages: int = Field(ge=0)


class ApiResponse(JavaApiModel, Generic[T]):
    success: bool
    code: str
    message: str
    data: T | None
    trace_id: str

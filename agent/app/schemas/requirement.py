"""Pydantic contracts shared by the backend client and later agent tools."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel


class JavaApiModel(BaseModel):
    """Model that maps Python snake_case fields to the Java API's camelCase JSON."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class RequirementStatus(StrEnum):
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
        values = self.model_dump(exclude_none=True, mode="json", by_alias=True)
        return {key: value for key, value in values.items() if value != ""}


T = TypeVar("T")


class PageResult(JavaApiModel, Generic[T]):
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

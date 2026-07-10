"""Typed exceptions for backend HTTP integration."""

from __future__ import annotations


class RequirementClientError(Exception):
    """Base error raised by the Java requirement client."""


class BackendTransportError(RequirementClientError):
    """The backend could not be reached or timed out."""


class BackendProtocolError(RequirementClientError):
    """The backend returned a response outside the documented contract."""


class BackendBusinessError(RequirementClientError):
    """The backend returned a documented business error response."""

    def __init__(self, code: str, message: str, trace_id: str | None, status_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.trace_id = trace_id
        self.status_code = status_code

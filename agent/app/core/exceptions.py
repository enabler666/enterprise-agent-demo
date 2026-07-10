"""Java 后端调用的异常分类。

工具层依异常类型转换为对用户安全的结果，不将 HTTP/连接细节直接暴露给最终用户。
"""

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


class AgentConfigurationError(Exception):
    """Agent 运行所需配置缺失，例如没有设置 DeepSeek API Key。"""

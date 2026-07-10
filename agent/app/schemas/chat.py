"""FastAPI 聊天接口的请求与响应模型。"""

from pydantic import Field, field_validator

from app.schemas.requirement import JavaApiModel


class ChatRequest(JavaApiModel):
    """客户端请求使用 userId/sessionId；Python 内部仍使用 snake_case。"""

    user_id: str = Field(min_length=1, max_length=128)
    session_id: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=4_000)

    @field_validator("user_id", "session_id", "message")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("不能为空")
        return value


class ChatResponse(JavaApiModel):
    answer: str
    user_id: str
    session_id: str

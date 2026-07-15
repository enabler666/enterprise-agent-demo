from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal, Protocol

from fastapi import FastAPI
from pydantic import BaseModel

from app.agent.service import ChatService
from app.api import chat_router
from app.core.config import Settings


class HealthResponse(BaseModel):
    """健康检查独立于 DeepSeek 和 Java 后端，用于探活。"""
    status: Literal["UP"]


class ChatServiceLike(Protocol):
    """应用工厂依赖的最小聊天服务接口，便于测试替换。"""

    async def start(self) -> None: ...

    async def close(self) -> None: ...


def create_app(chat_service: ChatServiceLike | None = None) -> FastAPI:
    """应用工厂允许测试注入假的 ChatService，避免真实模型和网络依赖。"""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await app.state.chat_service.start()
        try:
            yield
        finally:
            await app.state.chat_service.close()

    app = FastAPI(title="Enterprise Support Agent", version="0.1.0", lifespan=lifespan)
    app.state.chat_service = chat_service or ChatService(Settings.from_environment())
    app.include_router(chat_router)
    return app


app = create_app()


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="UP")

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """健康检查独立于 DeepSeek 和 Java 后端，用于探活。"""
    status: Literal["UP"]


app = FastAPI(title="Enterprise Support Agent", version="0.1.0")

# 路由层当前只保留探活；业务编排将在阶段 7 的 /chat 路由中注入 Agent 服务。


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="UP")

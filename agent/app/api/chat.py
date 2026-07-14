"""普通聊天与 SSE 流式聊天路由。"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app.agent.service import ChatService
from app.core.exceptions import AgentConfigurationError
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    """将用户消息交给需求 Agent；路由层不处理工具或模型流程。"""
    service: ChatService = request.app.state.chat_service
    try:
        return await service.chat(payload)
    except AgentConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


@router.post("/chat/stream")
async def stream_chat(payload: ChatRequest, request: Request) -> StreamingResponse:
    """以项目自有业务事件输出 SSE，不向路由暴露 LangGraph 原始事件。"""
    service: ChatService = request.app.state.chat_service

    # 下面的东西实际上是个Python方法，在方法里面写了个方法，可以不接受参数，直接获取外部方法的变量，叫做Python的闭包机制
    async def event_source() -> AsyncIterator[str]:
        # async for 循环，每次迭代返回一个异步事件，可以理解为有个while(True)的循环，async for算是语法糖
        async for event in service.stream_chat(payload):
            # 格式化返回事件变成Json
            data = json.dumps(asdict(event), ensure_ascii=False, separators=(",", ":"))
            # yield差不多意思是允许函数继续执行的return，但是不会阻塞函数的执行，而是返回一个异步迭代器
            yield f"event: {event.type}\ndata: {data}\n\n"

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

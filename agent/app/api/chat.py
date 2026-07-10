"""阶段 7 聊天路由。"""

from fastapi import APIRouter, HTTPException, Request, status

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

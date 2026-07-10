"""FastAPI 路由包；阶段 7 暴露聊天接口。"""

from app.api.chat import router as chat_router

__all__ = ["chat_router"]

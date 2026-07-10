"""聊天服务：连接 FastAPI 请求、会话历史与需求 Agent。"""

from __future__ import annotations

from typing import Protocol

from app.agent.graph import AgentRunResult, RequirementAgent, build_requirement_agent
from app.clients.requirement_client import RequirementClient
from app.core.config import Settings
from app.core.session_store import InMemorySessionStore
from app.schemas.chat import ChatRequest, ChatResponse
from app.tools.requirement_tools import RequirementTools


class RequirementAgentFactory(Protocol):
    def __call__(self, settings: Settings, tools: RequirementTools) -> RequirementAgent: ...


class ChatService:
    """处理单次聊天，并将 Agent 返回的消息历史保存到对应会话。"""

    def __init__(
        self,
        settings: Settings,
        session_store: InMemorySessionStore | None = None,
        agent_factory: RequirementAgentFactory = build_requirement_agent,
    ) -> None:
        self._settings = settings
        self._session_store = session_store or InMemorySessionStore()
        self._agent_factory = agent_factory
        self._client: RequirementClient | None = None
        self._agent: RequirementAgent | None = None

    async def chat(self, request: ChatRequest) -> ChatResponse:
        history = await self._session_store.get(request.user_id, request.session_id)
        result = await self._get_agent().ask(request.message, history=history)
        await self._session_store.save(request.user_id, request.session_id, result.history)
        return ChatResponse(
            answer=result.answer, user_id=request.user_id, session_id=request.session_id
        )

    async def close(self) -> None:
        """应用关闭时释放由 Client 持有的 HTTP 连接池。"""
        if self._client is not None:
            await self._client.close()

    def _get_agent(self) -> RequirementAgent:
        """惰性创建：/health 不需要模型 Key 或 Java 后端即可工作。"""
        if self._agent is None:
            self._client = RequirementClient(self._settings)
            tools = RequirementTools(self._client)
            self._agent = self._agent_factory(self._settings, tools)
        return self._agent

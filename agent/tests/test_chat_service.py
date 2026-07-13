import asyncio
from collections.abc import AsyncIterator
from typing import Any, cast

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.agent.events import AgentExecutionEvent, MessageEvent, StreamCompletedEvent
from app.agent.graph import AgentRunResult, RequirementAgent
from app.agent.service import ChatService
from app.core.config import Settings
from app.schemas.chat import ChatRequest


class FakeAgent:
    def __init__(self) -> None:
        self.histories: list[list[BaseMessage]] = []

    async def ask(self, user_message: str, history: list[BaseMessage] | None = None) -> AgentRunResult:
        prior_history = history or []
        self.histories.append(prior_history)
        messages = [*prior_history, HumanMessage(content=user_message), AIMessage(content="模拟回答")]
        return AgentRunResult(answer="模拟回答", history=messages)

    async def stream(
        self, user_message: str, history: list[BaseMessage] | None = None
    ) -> AsyncIterator[AgentExecutionEvent]:
        prior_history = history or []
        self.histories.append(prior_history)
        messages = [*prior_history, HumanMessage(content=user_message), AIMessage(content="流式回答")]
        yield MessageEvent(content="流式")
        yield MessageEvent(content="回答")
        yield StreamCompletedEvent(history=messages)


def test_chat_service_reuses_history_only_within_same_user_session() -> None:
    fake_agent = FakeAgent()

    def factory(_: Settings, __: Any) -> RequirementAgent:
        return cast(RequirementAgent, fake_agent)

    service = ChatService(Settings(), agent_factory=factory)

    async def run() -> None:
        await service.chat(ChatRequest(user_id="user-1", session_id="session-a", message="第一轮"))
        await service.chat(ChatRequest(user_id="user-1", session_id="session-a", message="第二轮"))
        await service.chat(ChatRequest(user_id="user-2", session_id="session-a", message="另一用户"))
        await service.close()

    asyncio.run(run())

    assert fake_agent.histories[0] == []
    assert len(fake_agent.histories[1]) == 2
    assert fake_agent.histories[2] == []


def test_stream_chat_saves_history_only_after_completion() -> None:
    fake_agent = FakeAgent()

    def factory(_: Settings, __: Any) -> RequirementAgent:
        return cast(RequirementAgent, fake_agent)

    service = ChatService(Settings(), agent_factory=factory)

    async def run() -> list[str]:
        request = ChatRequest(user_id="user-1", session_id="session-s", message="第一轮")
        first_types = [event.type async for event in service.stream_chat(request)]
        _ = [
            event
            async for event in service.stream_chat(
                ChatRequest(user_id="user-1", session_id="session-s", message="第二轮")
            )
        ]
        return first_types

    event_types = asyncio.run(run())

    assert event_types == ["message", "message", "done"]
    assert len(fake_agent.histories[1]) == 2

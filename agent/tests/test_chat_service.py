import asyncio
from typing import Any, cast

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

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

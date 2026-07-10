import asyncio
from typing import Any, cast

import pytest
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.runnables import Runnable

from app.agent.graph import RequirementAgent
from app.agent.model import create_deepseek_chat_model
from app.core.config import Settings
from app.core.exceptions import AgentConfigurationError
from app.schemas.requirement import Requirement, RequirementProgress, RequirementQuery
from app.tools.requirement_tools import RequirementTools


class FakeChatModel:
    """按顺序返回预设消息，并记录每次模型看到的完整上下文。"""

    def __init__(self, responses: list[AIMessage]) -> None:
        self.responses = responses
        self.inputs: list[list[BaseMessage]] = []

    async def ainvoke(self, messages: list[BaseMessage]) -> BaseMessage:
        self.inputs.append(messages)
        return self.responses.pop(0)


class StubBackend:
    async def get_requirement_by_no(
        self, requirement_no: str, trace_id: str | None = None
    ) -> Requirement:
        return Requirement.model_validate(
            {
                "id": 1,
                "requirementNo": requirement_no,
                "title": "新增生产服务器",
                "description": "采购两台生产服务器",
                "applicantId": "U001",
                "applicantName": "张伟",
                "department": "信息技术部",
                "type": "设备采购",
                "status": "PENDING_APPROVAL",
                "currentNode": "部门负责人审批",
                "expectedCompletionDate": "2026-08-15",
                "createdAt": "2026-07-01T09:00:00+08:00",
                "updatedAt": "2026-07-03T09:00:00+08:00",
            }
        )

    async def search_requirements(
        self, query: RequirementQuery, trace_id: str | None = None
    ) -> Any:
        raise AssertionError("本测试不应调用组合查询")

    async def get_requirement_progress(
        self, requirement_no: str, trace_id: str | None = None
    ) -> RequirementProgress:
        raise AssertionError("本测试不应调用进度查询")


def test_agent_calls_tool_then_generates_final_answer() -> None:
    fake_model = FakeChatModel(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_requirement_by_no",
                        "args": {"requirement_no": "XQ202607001"},
                        "id": "call-1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="需求 XQ202607001 当前处于部门负责人审批。"),
        ]
    )
    model = cast(Runnable[Any, BaseMessage], fake_model)
    agent = RequirementAgent(model, RequirementTools(StubBackend()))

    result = asyncio.run(agent.ask("查询 XQ202607001"))

    assert result.answer == "需求 XQ202607001 当前处于部门负责人审批。"
    assert any(isinstance(message, ToolMessage) for message in result.history)
    assert len(fake_model.inputs) == 2


def test_agent_accepts_previous_history_for_next_turn() -> None:
    first_model = FakeChatModel([AIMessage(content="请提供需求编号。")])
    first_agent = RequirementAgent(
        cast(Runnable[Any, BaseMessage], first_model), RequirementTools(StubBackend())
    )
    first = asyncio.run(first_agent.ask("帮我查一下需求"))

    second_model = FakeChatModel([AIMessage(content="好的，我来查询。")])
    second_agent = RequirementAgent(
        cast(Runnable[Any, BaseMessage], second_model), RequirementTools(StubBackend())
    )
    second = asyncio.run(second_agent.ask("编号是 XQ202607001", history=first.history))

    assert second.answer == "好的，我来查询。"
    # system message 之外，第二轮模型能看到第一轮历史和新用户消息。
    assert len(second_model.inputs[0]) >= 4


def test_missing_api_key_returns_configuration_error_without_network_call() -> None:
    with pytest.raises(AgentConfigurationError, match="DEEPSEEK_API_KEY"):
        create_deepseek_chat_model(Settings(deepseek_api_key=None))

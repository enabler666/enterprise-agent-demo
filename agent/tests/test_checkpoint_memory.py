import asyncio
from pathlib import Path
from typing import Any, cast

import pytest
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.runnables import Runnable
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from app.agent.graph import RequirementAgent
from app.tools.knowledge_tools import KnowledgeTools
from app.tools.requirement_tools import RequirementTools


class RecordingModel:
    def __init__(self, responses: list[AIMessage | Exception]) -> None:
        self.responses = responses
        self.inputs: list[list[BaseMessage]] = []

    async def ainvoke(self, messages: list[BaseMessage]) -> BaseMessage:
        self.inputs.append(messages)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class CountingBackend:
    def __init__(self) -> None:
        self.calls = 0

    async def get_requirement_by_no(
        self, requirement_no: str, trace_id: str | None = None
    ) -> Any:
        self.calls += 1
        raise RuntimeError("模拟未预期 Tool 异常")

    async def search_requirements(self, query: Any, trace_id: str | None = None) -> Any:
        raise AssertionError

    async def get_requirement_progress(
        self, requirement_no: str, trace_id: str | None = None
    ) -> Any:
        raise AssertionError


def make_agent(
    model: RecordingModel, checkpointer: Any, backend: Any | None = None
) -> RequirementAgent:
    return RequirementAgent(
        cast(Runnable[Any, BaseMessage], model),
        RequirementTools(backend or CountingBackend()),
        KnowledgeTools(None),
        checkpointer,
    )


def test_sessions_and_users_are_isolated_and_messages_are_not_duplicated() -> None:
    model = RecordingModel(
        [AIMessage(content="a1"), AIMessage(content="a2"), AIMessage(content="b1")]
    )
    agent = make_agent(model, InMemorySaver())

    async def run() -> None:
        await agent.ask("u1-s1-first", "u1-s1")
        await agent.ask("u1-s1-second", "u1-s1")
        await agent.ask("isolated", "u2-same-session")

    asyncio.run(run())

    assert [message.text for message in model.inputs[1][1:]] == [
        "u1-s1-first",
        "a1",
        "u1-s1-second",
    ]
    assert [message.text for message in model.inputs[2][1:]] == ["isolated"]


def test_tool_rounds_reset_and_unexpected_tool_failure_is_paired() -> None:
    def tool_call(call_id: str) -> AIMessage:
        return AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "get_requirement_by_no",
                    "args": {"requirement_no": "XQ202607001"},
                    "id": call_id,
                    "type": "tool_call",
                }
            ],
        )

    backend = CountingBackend()
    model = RecordingModel(
        [
            tool_call("call-1"),
            AIMessage(content="第一轮结束"),
            tool_call("call-2"),
            AIMessage(content="第二轮结束"),
        ]
    )
    agent = make_agent(model, InMemorySaver(), backend)

    async def run() -> tuple[list[BaseMessage], int]:
        await agent.ask("第一轮", "tool-thread")
        await agent.ask("第二轮", "tool-thread")
        snapshot = await agent.get_state("tool-thread")
        return list(snapshot.values["messages"]), snapshot.values["tool_rounds"]

    messages, tool_rounds = asyncio.run(run())

    assert backend.calls == 2
    assert tool_rounds == 1
    ai_calls = [
        message
        for message in messages
        if isinstance(message, AIMessage) and message.tool_calls
    ]
    tool_messages = [message for message in messages if isinstance(message, ToolMessage)]
    assert [message.tool_calls[0]["id"] for message in ai_calls] == [
        message.tool_call_id for message in tool_messages
    ]
    assert all("TOOL_EXECUTION_ERROR" in message.text for message in tool_messages)


def test_sqlite_checkpoint_restores_state_after_resources_restart(tmp_path: Path) -> None:
    database = tmp_path / "checkpoints.sqlite"

    async def run() -> tuple[list[BaseMessage], list[BaseMessage]]:
        first_model = RecordingModel([AIMessage(content="已记住编号。")])
        async with AsyncSqliteSaver.from_conn_string(str(database)) as first_saver:
            await first_saver.setup()
            first_agent = make_agent(first_model, first_saver)
            await first_agent.ask("请记住编号 XQ202607001", "restart-thread")
            before = list((await first_agent.get_state("restart-thread")).values["messages"])

        second_model = RecordingModel([AIMessage(content="编号是 XQ202607001。")])
        async with AsyncSqliteSaver.from_conn_string(str(database)) as second_saver:
            await second_saver.setup()
            second_agent = make_agent(second_model, second_saver)
            result = await second_agent.ask("我刚才提到的编号是什么？", "restart-thread")
            assert result.answer == "编号是 XQ202607001。"
            after = list((await second_agent.get_state("restart-thread")).values["messages"])
            assert len(second_model.inputs[0]) == 4
        return before, after

    before, after = asyncio.run(run())

    assert len(before) == 2
    assert len(after) == 4
    assert sum(
        isinstance(message, HumanMessage) and message.text == "请记住编号 XQ202607001"
        for message in after
    ) == 1


def test_model_failure_keeps_previous_checkpoint_legal() -> None:
    model = RecordingModel([AIMessage(content="稳定回答"), RuntimeError("model failed")])
    agent = make_agent(model, InMemorySaver())

    async def run() -> list[BaseMessage]:
        await agent.ask("成功轮次", "failure-thread")
        with pytest.raises(RuntimeError, match="model failed"):
            await agent.ask("失败轮次", "failure-thread")
        return list((await agent.get_state("failure-thread")).values["messages"])

    messages = asyncio.run(run())

    assert messages[0].text == "成功轮次"
    assert messages[1].text == "稳定回答"
    assert not any(isinstance(message, ToolMessage) for message in messages)


def test_stream_closed_by_client_does_not_store_token_chunks() -> None:
    model = RecordingModel([AIMessage(content="不会执行")])
    agent = make_agent(model, InMemorySaver())

    async def run() -> dict[str, Any]:
        stream = agent.stream("中断轮次", "cancelled-thread")
        first_event = await anext(stream)
        assert first_event.type == "status"
        await stream.aclose()
        return dict((await agent.get_state("cancelled-thread")).values)

    state = asyncio.run(run())

    assert state == {}
    assert model.inputs == []

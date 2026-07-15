import asyncio
from typing import Any, cast

import pytest
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.runnables import Runnable
from langgraph.checkpoint.memory import InMemorySaver

from app.agent.events import ToolEvent
from app.agent.graph import RequirementAgent
from app.agent.model import create_deepseek_chat_model
from app.agent.tool_schemas import requirement_tool_schemas
from app.core.config import Settings
from app.core.exceptions import AgentConfigurationError
from app.prompts.requirement_agent import REQUIREMENT_AGENT_SYSTEM_PROMPT
from app.rag.models import RetrievedChunk
from app.schemas.requirement import Requirement, RequirementProgress, RequirementQuery
from app.tools.knowledge_tools import KnowledgeTools
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
    agent = RequirementAgent(
        model, RequirementTools(StubBackend()), KnowledgeTools(None), InMemorySaver()
    )

    result = asyncio.run(agent.ask("查询 XQ202607001", thread_id="tool-test"))

    assert result.answer == "需求 XQ202607001 当前处于部门负责人审批。"
    assert any(isinstance(message, ToolMessage) for message in fake_model.inputs[-1])
    assert len(fake_model.inputs) == 2


def test_agent_restores_previous_thread_state_without_resubmitting_history() -> None:
    model = FakeChatModel(
        [AIMessage(content="已记住。"), AIMessage(content="编号是 XQ202607001。")]
    )
    agent = RequirementAgent(
        cast(Runnable[Any, BaseMessage], model),
        RequirementTools(StubBackend()),
        KnowledgeTools(None),
        InMemorySaver(),
    )

    async def run() -> None:
        await agent.ask("请记住编号 XQ202607001", thread_id="same-thread")
        await agent.ask("我刚才提到的编号是什么？", thread_id="same-thread")

    asyncio.run(run())

    assert len(model.inputs[0]) == 2
    assert len(model.inputs[1]) == 4


def test_missing_api_key_returns_configuration_error_without_network_call() -> None:
    with pytest.raises(AgentConfigurationError, match="DEEPSEEK_API_KEY"):
        create_deepseek_chat_model(Settings(deepseek_api_key=None))


class StubKnowledgeRetriever:
    def __init__(self) -> None:
        self.queries: list[tuple[str, int]] = []

    async def retrieve(self, query: str, top_k: int = 3) -> list[RetrievedChunk]:
        self.queries.append((query, top_k))
        return [
            RetrievedChunk(
                content="一级统筹是否经过由组织配置决定；分派和最终统筹不能取消。",
                chunk_id="internal-chunk-id",
                document_id="document-1",
                document_title="需求提报及流转相关说明",
                source="raw/需求提报及流转相关说明.md",
                chunk_index=2,
                distance=0.12,
            )
        ]


def test_knowledge_question_calls_tool_and_final_answer_has_unique_source() -> None:
    question = "一级统筹是不是必须经过？"
    final_answer = (
        "一级统筹并非所有组织都必须经过，是否启用由组织流程配置决定；"
        "分派和最终统筹是必须环节。\n\n"
        "参考来源：\n- 《需求提报及流转相关说明》，需求提报及流转相关说明.md"
    )
    fake_model = FakeChatModel(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "search_knowledge",
                        "args": {"query": question},
                        "id": "call-knowledge-1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content=final_answer),
        ]
    )
    retriever = StubKnowledgeRetriever()
    agent = RequirementAgent(
        cast(Runnable[Any, BaseMessage], fake_model),
        RequirementTools(StubBackend()),
        KnowledgeTools(retriever),
        InMemorySaver(),
    )

    result = asyncio.run(agent.ask(question, thread_id="knowledge-test"))

    assert retriever.queries == [(question, 3)]
    assert "参考来源" in result.answer
    assert result.answer.count("需求提报及流转相关说明.md") == 1
    tool_message = next(
        message for message in fake_model.inputs[-1] if isinstance(message, ToolMessage)
    )
    assert "document_title" in tool_message.text
    assert "distance" not in tool_message.text
    assert "internal-chunk-id" not in tool_message.text


def test_search_knowledge_stream_events_use_readable_label() -> None:
    fake_model = FakeChatModel(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "search_knowledge",
                        "args": {"query": "为什么删除和废弃不同？"},
                        "id": "call-knowledge-stream",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="根据知识资料，两者适用阶段和保留方式不同。"),
        ]
    )
    agent = RequirementAgent(
        cast(Runnable[Any, BaseMessage], fake_model),
        RequirementTools(StubBackend()),
        KnowledgeTools(StubKnowledgeRetriever()),
        InMemorySaver(),
    )

    async def collect() -> list[ToolEvent]:
        return [
            event
            async for event in agent.stream("为什么删除和废弃不同？", thread_id="stream-test")
            if isinstance(event, ToolEvent)
        ]

    events = asyncio.run(collect())

    assert [(event.tool, event.status) for event in events] == [
        ("企业知识库检索", "started"),
        ("企业知识库检索", "completed"),
    ]


def test_system_prompt_requires_grounded_knowledge_answers_and_sources() -> None:
    assert "必须调用 search_knowledge" in REQUIREMENT_AGENT_SYSTEM_PROMPT
    assert "不得编造业务规则" in REQUIREMENT_AGENT_SYSTEM_PROMPT
    assert "参考来源" in REQUIREMENT_AGENT_SYSTEM_PROMPT
    assert "相同文档只列一次" in REQUIREMENT_AGENT_SYSTEM_PROMPT
    assert "distance" in REQUIREMENT_AGENT_SYSTEM_PROMPT


def test_search_knowledge_schema_exposes_only_query() -> None:
    schema = next(
        item
        for item in requirement_tool_schemas()
        if item["function"]["name"] == "search_knowledge"
    )

    assert set(schema["function"]["parameters"]["properties"]) == {"query"}


def test_empty_knowledge_result_leads_to_explicit_insufficient_information_answer() -> None:
    class EmptyRetriever:
        async def retrieve(self, query: str, top_k: int = 3) -> list[RetrievedChunk]:
            return []

    fake_model = FakeChatModel(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "search_knowledge",
                        "args": {"query": "公司内部的未知审批规则是什么？"},
                        "id": "call-empty-knowledge",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="知识库中未找到足够信息，无法确认该内部规则。"),
        ]
    )
    agent = RequirementAgent(
        cast(Runnable[Any, BaseMessage], fake_model),
        RequirementTools(StubBackend()),
        KnowledgeTools(EmptyRetriever()),
        InMemorySaver(),
    )

    result = asyncio.run(
        agent.ask("公司内部的未知审批规则是什么？", thread_id="empty-test")
    )

    assert result.answer == "知识库中未找到足够信息，无法确认该内部规则。"
    tool_message = next(
        message for message in fake_model.inputs[-1] if isinstance(message, ToolMessage)
    )
    assert '"status":"NO_RESULT"' in tool_message.text
    assert '"data":null' in tool_message.text

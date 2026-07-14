"""需求查询 LangGraph 主流程。"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Literal

from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.runnables import Runnable
from langgraph.graph import END, START, StateGraph

from app.agent.events import (
    AgentExecutionEvent,
    MessageEvent,
    StatusEvent,
    StreamCompletedEvent,
    ToolEvent,
)
from app.agent.state import RequirementAgentState
from app.agent.tool_schemas import requirement_tool_schemas
from app.core.config import Settings
from app.prompts.requirement_agent import REQUIREMENT_AGENT_SYSTEM_PROMPT
from app.tools.requirement_tools import RequirementTools
from app.tools.result import ToolExecutionResult


@dataclass(frozen=True)
class AgentRunResult:
    """一次 Agent 执行结果；``history`` 可作为下一轮输入继续对话。"""

    answer: str
    history: list[BaseMessage]


class RequirementAgent:
    """由“模型判断 → 执行工具 → 模型回答”组成的只读工作流。"""

    def __init__(self, model: Runnable[Any, BaseMessage], tools: RequirementTools) -> None:
        self._model = model
        self._tools = tools
        builder = StateGraph(RequirementAgentState)
        # 节点只交换 State 的增量：messages 由 State 中的 reducer 追加，tool_rounds 用于限制
        # “模型请求工具 → 工具结果回注模型”的循环次数，避免异常模型响应造成无限调用。
        builder.add_node("model", self._call_model)
        builder.add_node("tools", self._execute_tools)
        builder.add_edge(START, "model")
        builder.add_conditional_edges("model", self._route_after_model, {"tools": "tools", "end": END})
        builder.add_edge("tools", "model")
        # LangGraph 必须 compile 后才可调用；编译会检查孤立节点和边连接。
        self._graph = builder.compile()
        # graph的可行一条路径 model(最开始注册模型时提供了tool) -> 语言模型返回了标准的json，表示需要一个工具调用 -> tools节点 -> model节点(查询信息放到了上下文,再次模型推理) -> end

    async def ask(
        self, user_message: str, history: list[BaseMessage] | None = None
    ) -> AgentRunResult:
        """执行一轮对话；调用方负责按 session 保存返回的 history。"""
        initial_messages = [*(history or []), HumanMessage(content=user_message)]
        state = await self._graph.ainvoke({"messages": initial_messages, "tool_rounds": 0})
        messages = list(state["messages"])
        last_message = messages[-1]
        answer = last_message.text if isinstance(last_message, AIMessage) else ""
        if not answer:
            answer = "暂时无法完成本次需求查询，请补充条件或稍后重试。"
        return AgentRunResult(answer=answer, history=messages)

    async def stream(
        self, user_message: str, history: list[BaseMessage] | None = None
    ) -> AsyncIterator[AgentExecutionEvent]:
        """将 LangGraph 原生流转换为稳定的业务事件，并返回最终完整历史。"""
        initial_messages = [*(history or []), HumanMessage(content=user_message)]
        completed_messages: list[BaseMessage] = []
        yield StatusEvent()

        async for mode, data in self._graph.astream(
            {"messages": initial_messages, "tool_rounds": 0},
            stream_mode=["messages", "updates"],
        ):
            if mode == "messages":
                chunk, metadata = data
                if metadata.get("langgraph_node") != "model":
                    continue
                if isinstance(chunk, AIMessageChunk) and not chunk.tool_call_chunks:
                    # DeepSeek reasoning_content 属于内部推理；这里只转发标准最终文本 content。
                    content = chunk.text
                    if content:
                        yield MessageEvent(content=content)
                continue

            if mode != "updates" or not isinstance(data, dict):
                continue
            for node_name, update in data.items():
                if not isinstance(update, dict):
                    continue
                messages = update.get("messages", [])
                if isinstance(messages, list):
                    completed_messages.extend(
                        message for message in messages if isinstance(message, BaseMessage)
                    )
                if node_name == "model":
                    for message in messages:
                        if isinstance(message, AIMessage):
                            for tool_call in message.tool_calls:
                                tool_name = tool_call.get("name", "")
                                yield self._tool_event(tool_name, "started")
                elif node_name == "tools":
                    for message in messages:
                        if isinstance(message, ToolMessage):
                            yield self._tool_event(message.name or "", "completed")

        # 内部完成事件让每个并发流携带自己的历史，不写入 Agent 共享状态。
        yield StreamCompletedEvent(history=[*initial_messages, *completed_messages])

    @staticmethod
    def _tool_event(name: str, status: Literal["started", "completed"]) -> ToolEvent:
        labels = {
            "get_requirement_by_no": "需求详情查询",
            "search_requirements": "需求组合查询",
            "get_requirement_progress": "需求进度查询",
        }
        label = labels.get(name, "需求查询")
        action = "正在执行" if status == "started" else "执行完成"
        return ToolEvent(tool=label, status=status, message=f"{label}{action}")

    async def _call_model(self, state: RequirementAgentState) -> dict[str, Any]:
        messages = [SystemMessage(content=REQUIREMENT_AGENT_SYSTEM_PROMPT), *state["messages"]]
        response = await self._model.ainvoke(messages)
        return {"messages": [response]}

    def _route_after_model(self, state: RequirementAgentState) -> Literal["tools", "end"]:
        # 仅 AIMessage 中的标准 tool_calls 才进入工具节点；没有工具调用时，该消息就是最终回答。
        last_message = state["messages"][-1]
        if (
            isinstance(last_message, AIMessage)
            and last_message.tool_calls
            and state.get("tool_rounds", 0) < 3
        ):
            return "tools"
        return "end"

    async def _execute_tools(self, state: RequirementAgentState) -> dict[str, Any]:
        last_message = state["messages"][-1]
        if not isinstance(last_message, AIMessage):
            return {"messages": [], "tool_rounds": state.get("tool_rounds", 0)}

        messages: list[ToolMessage] = []
        for tool_call in last_message.tool_calls:
            # LangChain 已按绑定的 JSON Schema 生成 name/args；ToolMessage 必须带回相同 id，
            # 以便下一次模型调用能将结果关联到原始工具调用。
            result = await self._dispatch_tool(tool_call["name"], tool_call["args"])
            messages.append(
                ToolMessage(
                    content=result.model_dump_json(),
                    tool_call_id=tool_call["id"],
                    name=tool_call["name"],
                )
            )
        return {"messages": messages, "tool_rounds": state.get("tool_rounds", 0) + 1}

    async def _dispatch_tool(self, name: str, arguments: object) -> ToolExecutionResult[Any]:
        if name == "get_requirement_by_no":
            return await self._tools.get_requirement_by_no(arguments)
        if name == "search_requirements":
            return await self._tools.search_requirements(arguments)
        if name == "get_requirement_progress":
            return await self._tools.get_requirement_progress(arguments)
        return ToolExecutionResult.failure(code="UNKNOWN_TOOL", message="不支持的查询操作")


def build_requirement_agent(settings: Settings, tools: RequirementTools) -> RequirementAgent:
    """生产环境工厂：创建 DeepSeek 模型并绑定三个只读工具 Schema。"""
    # 延迟导入避免仅启动健康检查时就初始化模型依赖或校验 API Key。
    from app.agent.model import create_deepseek_chat_model

    model = create_deepseek_chat_model(settings)
    model_with_tools = model.bind_tools(requirement_tool_schemas())
    return RequirementAgent(model_with_tools, tools)

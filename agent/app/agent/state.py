"""LangGraph 状态定义。"""

from typing import Annotated

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class RequirementAgentState(TypedDict):
    """图中各节点共享的状态。

``Annotated`` 将 ``add_messages`` 注册为 reducer；节点返回的新消息会追加到历史中，
Checkpointer 按 thread_id 恢复该字段。tool_rounds 只控制单次用户轮次，调用入口每轮重置。
"""

    messages: Annotated[list[AnyMessage], add_messages]
    tool_rounds: int

"""进程内会话历史存储；仅用于当前最小 Demo。"""

from __future__ import annotations

import asyncio

from langchain_core.messages import BaseMessage


class InMemorySessionStore:
    """按 userId/sessionId 保存最近消息。

当前数据随进程重启丢失，适合作为阶段 7 的最小实现；生产部署可在不改变
ChatService 接口的前提下替换为 Redis 或持久化存储。
"""

    def __init__(self, max_messages: int = 20) -> None:
        self._max_messages = max_messages
        self._sessions: dict[tuple[str, str], list[BaseMessage]] = {}
        # asyncio.Lock 避免同一进程的并发请求覆盖同一个会话历史。
        self._lock = asyncio.Lock()

    async def get(self, user_id: str, session_id: str) -> list[BaseMessage]:
        async with self._lock:
            return list(self._sessions.get((user_id, session_id), []))

    async def save(self, user_id: str, session_id: str, messages: list[BaseMessage]) -> None:
        async with self._lock:
            self._sessions[(user_id, session_id)] = list(messages[-self._max_messages :])

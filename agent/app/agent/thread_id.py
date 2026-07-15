"""LangGraph 线程标识生成规则。"""

from __future__ import annotations

import hashlib


def build_thread_id(user_id: str, session_id: str) -> str:
    """由已校验的用户与会话标识生成固定长度、稳定且无碰撞拼接歧义的 ID。"""
    payload = f"{len(user_id)}:{user_id}{len(session_id)}:{session_id}".encode()
    return f"chat-v1-{hashlib.sha256(payload).hexdigest()}"

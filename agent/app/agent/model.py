"""DeepSeek ChatModel 工厂。"""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_deepseek import ChatDeepSeek

from app.core.config import Settings
from app.core.exceptions import AgentConfigurationError


def create_deepseek_chat_model(settings: Settings) -> BaseChatModel:
    """按需创建模型 Client；健康检查和模块导入均不依赖 API Key。"""
    if settings.deepseek_api_key is None:
        raise AgentConfigurationError("未配置 DEEPSEEK_API_KEY，无法调用需求 Agent")

    return ChatDeepSeek(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        api_base=str(settings.deepseek_base_url).rstrip("/"),
        temperature=0,
        max_retries=2,
    )

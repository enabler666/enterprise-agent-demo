"""应用配置：在运行时从环境变量读取，不把密钥写入源码。"""

from __future__ import annotations

import os

from pydantic import BaseModel, Field, HttpUrl, SecretStr


class Settings(BaseModel):
    """运行配置。

``BaseModel`` 提供 Pydantic 的类型转换与校验；``SecretStr`` 在日志或 repr 中会脱敏，
避免 DeepSeek Key 被意外打印。
"""

    deepseek_api_key: SecretStr | None = Field(default=None, repr=False)
    deepseek_base_url: HttpUrl = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    backend_base_url: HttpUrl = "http://localhost:8080"
    backend_timeout_seconds: float = Field(default=10.0, gt=0, le=60)

    @classmethod
    def from_environment(cls) -> Settings:
        """显式读取环境变量。

不在模块导入时创建全局 Settings，测试可通过 ``monkeypatch`` 改写环境变量后再创建实例。
"""
        api_key = os.getenv("DEEPSEEK_API_KEY")
        return cls(
            deepseek_api_key=SecretStr(api_key) if api_key else None,
            deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            backend_base_url=os.getenv("BACKEND_BASE_URL", "http://localhost:8080"),
            backend_timeout_seconds=float(os.getenv("BACKEND_TIMEOUT_SECONDS", "10")),
        )

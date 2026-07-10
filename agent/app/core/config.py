"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os

from pydantic import BaseModel, Field, HttpUrl, SecretStr


class Settings(BaseModel):
    """Runtime settings; secrets are intentionally represented as ``SecretStr``."""

    deepseek_api_key: SecretStr | None = Field(default=None, repr=False)
    deepseek_base_url: HttpUrl = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    backend_base_url: HttpUrl = "http://localhost:8080"
    backend_timeout_seconds: float = Field(default=10.0, gt=0, le=60)

    @classmethod
    def from_environment(cls) -> Settings:
        """Create settings without logging or exposing the API key."""
        api_key = os.getenv("DEEPSEEK_API_KEY")
        return cls(
            deepseek_api_key=SecretStr(api_key) if api_key else None,
            deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            backend_base_url=os.getenv("BACKEND_BASE_URL", "http://localhost:8080"),
            backend_timeout_seconds=float(os.getenv("BACKEND_TIMEOUT_SECONDS", "10")),
        )

"""Embedding 抽象及硅基流动 HTTP 实现。"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, cast

import httpx
from pydantic import SecretStr


class EmbeddingError(Exception):
    """Embedding 请求或响应不符合约定。"""


class EmbeddingProvider(Protocol):
    """将文档或查询文本转换为同一向量空间。"""

    @property
    def model_name(self) -> str: ...

    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    async def embed_query(self, text: str) -> list[float]: ...


class SiliconFlowEmbeddingProvider:
    """通过 OpenAI-compatible embeddings 接口批量生成向量。"""

    def __init__(
        self,
        api_key: SecretStr,
        base_url: str,
        model_name: str,
        timeout_seconds: float = 30.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._model_name = model_name
        self._client = client or httpx.AsyncClient(
            base_url=f"{base_url.rstrip('/')}/", timeout=timeout_seconds
        )
        self._owns_client = client is None
        self._headers = {"Authorization": f"Bearer {api_key.get_secret_value()}"}

    @property
    def model_name(self) -> str:
        return self._model_name

    async def __aenter__(self) -> SiliconFlowEmbeddingProvider:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    async def close(self) -> None:
        """释放由 Provider 自己创建的 HTTP 连接池。"""
        if self._owns_client:
            await self._client.aclose()

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if any(not text.strip() for text in texts):
            raise EmbeddingError("文档文本不得为空")
        return await self._embed(texts)

    async def embed_query(self, text: str) -> list[float]:
        if not text.strip():
            raise EmbeddingError("查询文本不得为空")
        return (await self._embed([text]))[0]

    async def _embed(self, texts: list[str]) -> list[list[float]]:
        try:
            response = await self._client.post(
                "embeddings",
                headers=self._headers,
                json={"model": self._model_name, "input": texts},
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise EmbeddingError("Embedding 请求超时") from exc
        except httpx.HTTPStatusError as exc:
            raise EmbeddingError(f"Embedding 服务返回 HTTP {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise EmbeddingError("无法连接 Embedding 服务") from exc

        try:
            payload = cast(dict[str, object], response.json())
            raw_data = cast(Sequence[object], payload["data"])
            indexed = []
            for item in raw_data:
                entry = cast(dict[str, object], item)
                index = int(cast(int, entry["index"]))
                vector = [float(value) for value in cast(Sequence[object], entry["embedding"])]
                if not vector:
                    raise ValueError
                indexed.append((index, vector))
            indexed.sort(key=lambda pair: pair[0])
        except (KeyError, TypeError, ValueError) as exc:
            raise EmbeddingError("Embedding 服务返回结构异常") from exc

        embeddings = [vector for _, vector in indexed]
        if len(embeddings) != len(texts):
            raise EmbeddingError(
                f"Embedding 向量数量不匹配：输入 {len(texts)} 条，返回 {len(embeddings)} 条"
            )
        if [index for index, _ in indexed] != list(range(len(texts))):
            raise EmbeddingError("Embedding 服务返回的向量索引异常")
        return embeddings

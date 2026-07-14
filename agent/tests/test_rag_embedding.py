from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

import httpx
import pytest
from pydantic import SecretStr

from app.rag.embedding import EmbeddingError, SiliconFlowEmbeddingProvider


def test_embeds_documents_in_one_batch_request() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "data": [
                    {"index": 0, "embedding": [1.0, 0.0]},
                    {"index": 1, "embedding": [0.0, 1.0]},
                ]
            },
        )

    provider = make_provider(handler)
    embeddings = asyncio.run(provider.embed_documents(["第一段", "第二段"]))

    assert embeddings == [[1.0, 0.0], [0.0, 1.0]]
    assert len(requests) == 1
    assert requests[0].url.path == "/v1/embeddings"


def test_rejects_embedding_count_mismatch() -> None:
    provider = make_provider(
        lambda request: httpx.Response(
            200, json={"data": [{"index": 0, "embedding": [1.0]}]}
        )
    )

    with pytest.raises(EmbeddingError, match="向量数量不匹配"):
        asyncio.run(provider.embed_documents(["第一段", "第二段"]))


def test_empty_document_list_does_not_send_request() -> None:
    called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(500)

    provider = make_provider(handler)

    assert asyncio.run(provider.embed_documents([])) == []
    assert called is False


def test_empty_query_is_rejected_without_request() -> None:
    provider = make_provider(lambda request: httpx.Response(500))

    with pytest.raises(EmbeddingError, match="查询文本不得为空"):
        asyncio.run(provider.embed_query("  \n"))


def test_reports_http_and_malformed_response_errors() -> None:
    failed = make_provider(lambda request: httpx.Response(429))
    malformed = make_provider(lambda request: httpx.Response(200, json={"unexpected": []}))

    with pytest.raises(EmbeddingError, match="HTTP 429"):
        asyncio.run(failed.embed_query("问题"))
    with pytest.raises(EmbeddingError, match="返回结构异常"):
        asyncio.run(malformed.embed_query("问题"))


MockHandler = Callable[[httpx.Request], httpx.Response | Awaitable[httpx.Response]]


def make_provider(handler: MockHandler) -> SiliconFlowEmbeddingProvider:
    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(base_url="https://api.example.com/v1/", transport=transport)
    return SiliconFlowEmbeddingProvider(
        SecretStr("test-key"),
        "https://ignored.example.com/v1",
        "test-model",
        client=client,
    )

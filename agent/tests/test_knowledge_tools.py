from __future__ import annotations

import asyncio
from pathlib import Path

from app.rag.embedding import EmbeddingError
from app.rag.models import RetrievedChunk
from app.rag.vector_store import VectorStoreError
from app.tools.knowledge_tools import KnowledgeTools
from app.tools.result import ToolExecutionStatus


class FakeRetriever:
    def __init__(
        self,
        results: list[RetrievedChunk] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.results = results or []
        self.error = error
        self.calls: list[tuple[str, int]] = []

    async def retrieve(self, query: str, top_k: int = 3) -> list[RetrievedChunk]:
        self.calls.append((query, top_k))
        if self.error is not None:
            raise self.error
        return self.results


def make_chunk(source: str = "raw/需求提报及流转相关说明.md") -> RetrievedChunk:
    return RetrievedChunk(
        content="删除和废弃是不同业务操作，适用阶段与数据保留方式不同。",
        chunk_id="private-chunk-id",
        document_id="private-document-id",
        document_title="需求提报及流转相关说明",
        source=source,
        chunk_index=4,
        distance=0.08,
    )


def test_search_knowledge_validates_query_without_calling_retriever() -> None:
    retriever = FakeRetriever([make_chunk()])

    blank = asyncio.run(KnowledgeTools(retriever).search_knowledge({"query": "  "}))
    unsupported_top_k = asyncio.run(
        KnowledgeTools(retriever).search_knowledge({"query": "流程", "top_k": 5})
    )

    assert blank.status is ToolExecutionStatus.ERROR
    assert blank.code == "INVALID_ARGUMENT"
    assert unsupported_top_k.code == "INVALID_ARGUMENT"
    assert retriever.calls == []


def test_search_knowledge_calls_retriever_and_returns_safe_citable_fields(
    tmp_path: Path,
) -> None:
    absolute_source = str(tmp_path / "需求提报及流转相关说明.md")
    retriever = FakeRetriever([make_chunk(absolute_source)])

    result = asyncio.run(
        KnowledgeTools(retriever).search_knowledge({"query": " 为什么删除和废弃不同？ "})
    )

    assert retriever.calls == [("为什么删除和废弃不同？", 3)]
    assert result.status is ToolExecutionStatus.SUCCESS
    assert result.data is not None
    assert result.data[0].rank == 1
    assert result.data[0].document_title == "需求提报及流转相关说明"
    assert result.data[0].source == "需求提报及流转相关说明.md"
    assert result.data[0].chunk_index == 4
    assert "删除和废弃" in result.data[0].content
    serialized = result.model_dump_json()
    assert str(tmp_path) not in serialized
    assert "distance" not in serialized
    assert "embedding" not in serialized.lower()
    assert "private-chunk-id" not in serialized


def test_search_knowledge_returns_no_result_without_inventing_content() -> None:
    result = asyncio.run(KnowledgeTools(FakeRetriever()).search_knowledge({"query": "未知规则"}))

    assert result.status is ToolExecutionStatus.NO_RESULT
    assert result.data is None
    assert result.message == "知识库中未找到足够信息"


def test_search_knowledge_reports_missing_configuration_and_known_failures() -> None:
    missing_key = asyncio.run(KnowledgeTools(None).search_knowledge({"query": "流程规则"}))
    mismatch = asyncio.run(
        KnowledgeTools(
            FakeRetriever(error=VectorStoreError("当前 Embedding 模型与索引模型不一致"))
        ).search_knowledge({"query": "流程规则"})
    )
    missing_index = asyncio.run(
        KnowledgeTools(
            FakeRetriever(error=VectorStoreError("尚未建立知识索引，请先运行索引构建命令"))
        ).search_knowledge({"query": "流程规则"})
    )
    embedding_failure = asyncio.run(
        KnowledgeTools(FakeRetriever(error=EmbeddingError("timeout"))).search_knowledge(
            {"query": "流程规则"}
        )
    )

    assert missing_key.code == "EMBEDDING_NOT_CONFIGURED"
    assert "SILICONFLOW_API_KEY" in missing_key.message
    assert mismatch.code == "EMBEDDING_MODEL_MISMATCH"
    assert "不一致" in mismatch.message
    assert missing_index.code == "KNOWLEDGE_INDEX_NOT_READY"
    assert "尚未建立知识索引" in missing_index.message
    assert embedding_failure.code == "EMBEDDING_REQUEST_FAILED"


def test_search_knowledge_hides_unknown_chroma_failure_details() -> None:
    result = asyncio.run(
        KnowledgeTools(
            FakeRetriever(error=RuntimeError("C:/secret/chroma/internal"))
        ).search_knowledge({"query": "流程规则"})
    )

    assert result.code == "KNOWLEDGE_SEARCH_FAILED"
    assert "secret" not in result.message
    assert "chroma" not in result.message.lower()

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from app.rag.embedding import EmbeddingProvider
from app.rag.indexer import KnowledgeIndexer
from app.rag.retriever import KnowledgeRetriever
from app.rag.vector_store import ChromaVectorStore, VectorStoreError


class FakeEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model_name: str = "fake-business-v1") -> None:
        self._model_name = model_name
        self.document_calls: list[list[str]] = []

    @property
    def model_name(self) -> str:
        return self._model_name

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.document_calls.append(texts)
        return [vector_for(text) for text in texts]

    async def embed_query(self, text: str) -> list[float]:
        if not text.strip():
            raise ValueError("查询文本不得为空")
        return vector_for(text)


def vector_for(text: str) -> list[float]:
    return [
        float("删除" in text or "废弃" in text),
        float("一级统筹" in text or "流程" in text),
        float("预算" in text),
    ]


def test_indexer_batches_chunks_and_rebuild_has_no_duplicates(tmp_path: Path) -> None:
    knowledge_root = make_knowledge_base(tmp_path)
    provider = FakeEmbeddingProvider()
    store = ChromaVectorStore(tmp_path / "chroma", "test_collection")
    indexer = KnowledgeIndexer(knowledge_root, provider, store)

    first = asyncio.run(indexer.rebuild())
    second = asyncio.run(indexer.rebuild())

    assert len(provider.document_calls) == 2
    assert all(len(call) == first.chunk_count for call in provider.document_calls)
    assert first.written_count == first.chunk_count
    assert second.written_count == first.written_count


def test_retrieval_keeps_metadata_top_k_and_stable_order(tmp_path: Path) -> None:
    provider = FakeEmbeddingProvider()
    store = ChromaVectorStore(tmp_path / "chroma", "test_collection")
    asyncio.run(KnowledgeIndexer(make_knowledge_base(tmp_path), provider, store).rebuild())
    retriever = KnowledgeRetriever(provider, store)

    first = asyncio.run(retriever.retrieve("为什么删除和废弃是两个操作", top_k=1))
    second = asyncio.run(retriever.retrieve("为什么删除和废弃是两个操作", top_k=1))

    assert len(first) == 1
    assert "删除" in first[0].content or "废弃" in first[0].content
    assert first[0].source == "rules.md"
    assert first[0].document_title == "需求规则"
    assert first[0].chunk_index >= 0
    assert first[0].distance is not None
    assert [item.chunk_id for item in first] == [item.chunk_id for item in second]

    tied_first = asyncio.run(retriever.retrieve("无关键词问题", top_k=3))
    tied_second = asyncio.run(retriever.retrieve("无关键词问题", top_k=3))
    assert [item.chunk_id for item in tied_first] == [item.chunk_id for item in tied_second]
    assert [item.chunk_id for item in tied_first] == sorted(
        item.chunk_id for item in tied_first
    )


def test_process_question_hits_process_rule(tmp_path: Path) -> None:
    provider = FakeEmbeddingProvider()
    store = ChromaVectorStore(tmp_path / "chroma", "test_collection")
    asyncio.run(KnowledgeIndexer(make_knowledge_base(tmp_path), provider, store).rebuild())

    [result] = asyncio.run(
        KnowledgeRetriever(provider, store).retrieve("一级统筹是不是必须经过", top_k=1)
    )

    assert "一级统筹" in result.content or "流程" in result.content


def test_missing_index_and_model_mismatch_are_explicit(tmp_path: Path) -> None:
    store = ChromaVectorStore(tmp_path / "chroma", "test_collection")
    provider = FakeEmbeddingProvider()

    with pytest.raises(VectorStoreError, match="尚未建立知识索引"):
        asyncio.run(KnowledgeRetriever(provider, store).retrieve("问题"))

    asyncio.run(KnowledgeIndexer(make_knowledge_base(tmp_path), provider, store).rebuild())
    changed_provider = FakeEmbeddingProvider("fake-business-v2")
    with pytest.raises(VectorStoreError, match="模型与索引模型不一致"):
        asyncio.run(KnowledgeRetriever(changed_provider, store).retrieve("问题"))


def make_knowledge_base(tmp_path: Path) -> Path:
    root = tmp_path / "knowledge"
    root.mkdir(exist_ok=True)
    (root / "rules.md").write_text(
        "# 需求规则\n\n"
        "删除只适用于误建且尚未流转的需求；废弃用于已经进入管理流程但不再继续的需求。",
        encoding="utf-8",
    )
    (root / "flow.md").write_text(
        "# 流程规则\n\n一级统筹是否必须经过取决于组织流程配置。",
        encoding="utf-8",
    )
    (root / "budget.md").write_text(
        "# 预算规则\n\n预算规则要求填写金额。",
        encoding="utf-8",
    )
    return root

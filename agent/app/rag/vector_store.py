"""向量存储抽象及 Chroma 本地持久化实现。"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, cast

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.errors import NotFoundError

from app.rag.models import KnowledgeChunk, RetrievedChunk


class VectorStoreError(Exception):
    """向量索引状态或内容不符合检索要求。"""


class VectorStore(Protocol):
    @property
    def collection_name(self) -> str: ...

    @property
    def persist_directory(self) -> Path: ...

    def rebuild(
        self,
        chunks: list[KnowledgeChunk],
        embeddings: list[list[float]],
        embedding_model: str,
    ) -> int: ...

    def search(
        self, query_embedding: list[float], top_k: int, embedding_model: str
    ) -> list[RetrievedChunk]: ...


class ChromaVectorStore:
    """使用 Chroma PersistentClient 保存及查询知识块。"""

    def __init__(self, persist_directory: Path, collection_name: str) -> None:
        self._persist_directory = persist_directory.resolve()
        self._persist_directory.mkdir(parents=True, exist_ok=True)
        self._collection_name = collection_name
        self._client = chromadb.PersistentClient(path=str(self._persist_directory))

    @property
    def collection_name(self) -> str:
        return self._collection_name

    @property
    def persist_directory(self) -> Path:
        return self._persist_directory

    def rebuild(
        self,
        chunks: list[KnowledgeChunk],
        embeddings: list[list[float]],
        embedding_model: str,
    ) -> int:
        if len(chunks) != len(embeddings):
            raise VectorStoreError("chunk 数量与向量数量不匹配")
        try:
            self._client.delete_collection(self._collection_name)
        except (NotFoundError, ValueError):
            pass
        collection = self._client.create_collection(
            self._collection_name,
            metadata={"embedding_model": embedding_model},
        )
        if chunks:
            collection.upsert(
                ids=[chunk.id for chunk in chunks],
                embeddings=embeddings,
                documents=[chunk.content for chunk in chunks],
                metadatas=[self._metadata(chunk, embedding_model) for chunk in chunks],
            )
        return collection.count()

    def search(
        self, query_embedding: list[float], top_k: int, embedding_model: str
    ) -> list[RetrievedChunk]:
        if top_k <= 0:
            raise VectorStoreError("top_k 必须大于 0")
        collection = self._existing_collection()
        indexed_model = (collection.metadata or {}).get("embedding_model")
        if indexed_model != embedding_model:
            raise VectorStoreError("当前 Embedding 模型与索引模型不一致，请重新构建索引。")
        if collection.count() == 0:
            raise VectorStoreError("尚未建立知识索引，请先运行索引构建命令。")

        result = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )
        ids = (result.get("ids") or [[]])[0]
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        retrieved = []
        for chunk_id, content, metadata, distance in zip(
            ids, documents, metadatas, distances, strict=True
        ):
            if content is None or metadata is None:
                raise VectorStoreError("Chroma 检索结果缺少正文或 metadata")
            retrieved.append(
                RetrievedChunk(
                    content=content,
                    chunk_id=chunk_id,
                    document_id=str(metadata["document_id"]),
                    document_title=str(metadata["document_title"]),
                    source=str(metadata["source"]),
                    chunk_index=int(cast(int, metadata["chunk_index"])),
                    distance=float(distance) if distance is not None else None,
                )
            )
        # distance 相同时使用稳定 chunk ID 打破平局。
        return sorted(
            retrieved,
            key=lambda item: (
                item.distance if item.distance is not None else float("inf"), item.chunk_id
            ),
        )

    def _existing_collection(self) -> Collection:
        try:
            return self._client.get_collection(self._collection_name)
        except (NotFoundError, ValueError) as exc:
            raise VectorStoreError("尚未建立知识索引，请先运行索引构建命令。") from exc

    @staticmethod
    def _metadata(chunk: KnowledgeChunk, embedding_model: str) -> dict[str, str | int]:
        return {
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "document_title": chunk.document_title,
            "source": chunk.source,
            "chunk_index": chunk.chunk_index,
            "embedding_model": embedding_model,
        }

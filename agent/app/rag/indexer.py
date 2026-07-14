"""知识库完整重建命令。"""
# 索引建立入口

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings
from app.rag.document_loader import MarkdownDocumentLoader
from app.rag.embedding import EmbeddingProvider, SiliconFlowEmbeddingProvider
from app.rag.text_splitter import MarkdownTextSplitter
from app.rag.vector_store import ChromaVectorStore, VectorStore

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_KNOWLEDGE_ROOT = _REPOSITORY_ROOT / "knowledge"


# 意思是创建之后不可变的，用于做返回值的实体类，没什么用
@dataclass(frozen=True)
class IndexSummary:
    knowledge_root: Path
    document_count: int
    chunk_count: int
    embedding_model: str
    collection_name: str
    persist_directory: Path
    written_count: int


class KnowledgeIndexer:
    """协调文档加载、切分、批量向量化及完整索引重建。"""

    def __init__(
        self,
        knowledge_root: Path,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        self._knowledge_root = knowledge_root
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

    async def rebuild(self) -> IndexSummary:
        documents = MarkdownDocumentLoader(self._knowledge_root).load()
        chunks = MarkdownTextSplitter().split_all(documents)
        embeddings = await self._embedding_provider.embed_documents(
            [chunk.content for chunk in chunks]
        )
        written_count = self._vector_store.rebuild(
            chunks, embeddings, self._embedding_provider.model_name
        )
        return IndexSummary(
            knowledge_root=self._knowledge_root.resolve(),
            document_count=len(documents),
            chunk_count=len(chunks),
            embedding_model=self._embedding_provider.model_name,
            collection_name=self._vector_store.collection_name,
            persist_directory=self._vector_store.persist_directory,
            written_count=written_count,
        )


async def _run() -> None:
    settings = Settings.from_environment()
    if settings.siliconflow_api_key is None:
        raise RuntimeError("缺少 SILICONFLOW_API_KEY，无法构建知识索引。")
    configured_root = os.getenv("KNOWLEDGE_ROOT")
    knowledge_root = Path(configured_root) if configured_root else _DEFAULT_KNOWLEDGE_ROOT
    store = ChromaVectorStore(
        settings.chroma_persist_directory, settings.chroma_collection_name
    )
    # 意义是类似Java的try-with-resources，执行__aexit__方法，确保资源被正确释放
    async with SiliconFlowEmbeddingProvider(
        settings.siliconflow_api_key,
        str(settings.siliconflow_base_url),
        settings.siliconflow_embedding_model,
    ) as provider:
        summary = await KnowledgeIndexer(knowledge_root, provider, store).rebuild()
    print(f"知识库目录：{summary.knowledge_root}")
    print(f"文档数量：{summary.document_count}")
    print(f"chunk 数量：{summary.chunk_count}")
    print(f"Embedding 模型：{summary.embedding_model}")
    print(f"collection：{summary.collection_name}")
    print(f"持久化目录：{summary.persist_directory}")
    print(f"实际写入数量：{summary.written_count}")


def main() -> None:
    # 这个是允许运行异步函数的入口，至于为什么是异步:因为rebuild是异步，因为调用向量化接口是异步，所以全都是异步的
    asyncio.run(_run())


if __name__ == "__main__":
    main()

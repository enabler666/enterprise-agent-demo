"""协调查询向量化与向量检索。"""

from app.rag.embedding import EmbeddingProvider
from app.rag.models import RetrievedChunk
from app.rag.vector_store import VectorStore


class KnowledgeRetriever:
    def __init__(self, embedding_provider: EmbeddingProvider, vector_store: VectorStore) -> None:
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

    async def retrieve(self, query: str, top_k: int = 3) -> list[RetrievedChunk]:
        query_embedding = await self._embedding_provider.embed_query(query)
        return self._vector_store.search(
            query_embedding, top_k, self._embedding_provider.model_name
        )

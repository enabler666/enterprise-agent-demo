"""将现有知识库召回能力封装为 Agent Tool。"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.rag.embedding import EmbeddingError
from app.rag.models import RetrievedChunk
from app.rag.vector_store import VectorStoreError
from app.tools.result import ToolExecutionResult


class KnowledgeRetrieverLike(Protocol):
    async def retrieve(self, query: str, top_k: int = 3) -> list[RetrievedChunk]: ...


class SearchKnowledgeInput(BaseModel):
    """模型只提供问题文本，召回数量由 Tool 固定控制。"""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=2000)

    @field_validator("query", mode="before")
    @classmethod
    def strip_query(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class KnowledgeSearchItem(BaseModel):
    """提供给模型的可引用资料，不包含向量与内部检索字段。"""

    model_config = ConfigDict(frozen=True)

    rank: int = Field(ge=1)
    document_title: str
    source: str
    chunk_index: int = Field(ge=0)
    content: str


class KnowledgeTools:
    """查询企业需求管理业务文档。"""

    def __init__(self, retriever: KnowledgeRetrieverLike | None) -> None:
        self._retriever = retriever

    async def search_knowledge(
        self, payload: object
    ) -> ToolExecutionResult[list[KnowledgeSearchItem]]:
        try:
            input_data = SearchKnowledgeInput.model_validate(payload)
        except ValidationError as error:
            return ToolExecutionResult.invalid_arguments(error)

        if self._retriever is None:
            return ToolExecutionResult.failure(
                code="EMBEDDING_NOT_CONFIGURED",
                message="知识库检索未配置 SILICONFLOW_API_KEY",
            )

        try:
            chunks = await self._retriever.retrieve(input_data.query, top_k=3)
        except EmbeddingError:
            return ToolExecutionResult.failure(
                code="EMBEDDING_REQUEST_FAILED",
                message="知识查询向量化失败，请稍后重试",
            )
        except VectorStoreError as error:
            return self._map_vector_store_error(error)
        except Exception:
            # Chroma 或替换实现的未知异常统一收敛，不向模型暴露底层堆栈。
            return ToolExecutionResult.failure(
                code="KNOWLEDGE_SEARCH_FAILED",
                message="知识库检索失败，请稍后重试",
            )

        if not chunks:
            return ToolExecutionResult.no_result(message="知识库中未找到足够信息")

        items = [
            KnowledgeSearchItem(
                rank=rank,
                document_title=chunk.document_title,
                source=self._safe_source_name(chunk.source),
                chunk_index=chunk.chunk_index,
                content=chunk.content,
            )
            for rank, chunk in enumerate(chunks, start=1)
        ]
        return ToolExecutionResult.success(items, message=f"共检索到 {len(items)} 条相关业务资料")

    @staticmethod
    def _safe_source_name(source: str) -> str:
        """仅返回文件名，避免异常索引元数据泄露本机目录。"""
        return PurePosixPath(source.replace("\\", "/")).name

    @staticmethod
    def _map_vector_store_error(
        error: VectorStoreError,
    ) -> ToolExecutionResult[list[KnowledgeSearchItem]]:
        message = str(error)
        if "模型与索引模型不一致" in message:
            return ToolExecutionResult.failure(
                code="EMBEDDING_MODEL_MISMATCH",
                message="当前 Embedding 模型与知识索引不一致，请重新构建索引",
            )
        if "尚未建立知识索引" in message:
            return ToolExecutionResult.failure(
                code="KNOWLEDGE_INDEX_NOT_READY",
                message="尚未建立知识索引，请先运行索引构建命令",
            )
        return ToolExecutionResult.failure(
            code="KNOWLEDGE_SEARCH_FAILED",
            message="知识库检索失败，请稍后重试",
        )

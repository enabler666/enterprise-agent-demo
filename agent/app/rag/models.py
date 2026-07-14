"""RAG 文档加载与切分阶段使用的统一数据模型。"""

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeDocument(BaseModel):
    """从知识库加载的一篇完整业务文档。"""

    model_config = ConfigDict(frozen=True)

    id: str
    title: str
    source: str
    content: str


class KnowledgeChunk(BaseModel):
    """保留来源信息的一段知识文档文本。"""

    model_config = ConfigDict(frozen=True)

    id: str
    document_id: str
    content: str
    source: str
    document_title: str
    chunk_index: int = Field(ge=0)

"""面向中文 Markdown 业务文档的文本切分器。"""

from __future__ import annotations

import hashlib
import re

from app.rag.models import KnowledgeChunk, KnowledgeDocument

# 700 字符通常可容纳一个完整业务小节；100 字符重叠用于保留边界处的上下文。
DEFAULT_CHUNK_SIZE = 700
DEFAULT_CHUNK_OVERLAP = 100
_PARAGRAPH_BOUNDARY = re.compile(r"\n\s*\n+")
_SENTENCE_ENDINGS = "。！？；.!?;\n"


class MarkdownTextSplitter:
    """优先按 Markdown 标题和自然段边界切分，超长段落再按句末切分。"""

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size 必须大于 0")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap 必须大于等于 0 且小于 chunk_size")
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def split(self, document: KnowledgeDocument) -> list[KnowledgeChunk]:
        """按原文顺序切分一篇文档，并为每个非空文本块补充稳定元数据。"""
        contents = self._split_content(document.content)
        return [
            KnowledgeChunk(
                id=_stable_chunk_id(document.id, index, content),
                document_id=document.id,
                content=content,
                source=document.source,
                document_title=document.title,
                chunk_index=index,
            )
            for index, content in enumerate(contents)
        ]

    def split_all(self, documents: list[KnowledgeDocument]) -> list[KnowledgeChunk]:
        """保持文档及文档内部顺序，依次切分多篇文档。"""
        return [chunk for document in documents for chunk in self.split(document)]

    def _split_content(self, content: str) -> list[str]:
        units = [unit.strip() for unit in _PARAGRAPH_BOUNDARY.split(content) if unit.strip()]
        chunks: list[str] = []
        current = ""

        for unit in units:
            if len(unit) > self._chunk_size:
                if current:
                    chunks.append(current)
                    current = ""
                chunks.extend(self._split_long_unit(unit))
                continue

            candidate = unit if not current else f"{current}\n\n{unit}"
            if len(candidate) <= self._chunk_size:
                current = candidate
                continue

            chunks.append(current)
            overlap = self._overlap_suffix(current)
            current = f"{overlap}\n\n{unit}" if overlap else unit

        if current:
            chunks.append(current)
        return [chunk.strip() for chunk in chunks if chunk.strip()]

    def _split_long_unit(self, text: str) -> list[str]:
        chunks: list[str] = []
        start = 0
        while start < len(text):
            proposed_end = min(start + self._chunk_size, len(text))
            end = self._preferred_boundary(text, start, proposed_end)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(text):
                break
            start = max(end - self._chunk_overlap, start + 1)
        return chunks

    def _preferred_boundary(self, text: str, start: int, proposed_end: int) -> int:
        if proposed_end >= len(text):
            return len(text)
        minimum_end = start + self._chunk_size // 2
        for index in range(proposed_end - 1, minimum_end - 1, -1):
            if text[index] in _SENTENCE_ENDINGS:
                return index + 1
        return proposed_end

    def _overlap_suffix(self, text: str) -> str:
        if self._chunk_overlap == 0:
            return ""
        suffix = text[-self._chunk_overlap :]
        # 从重叠区内第一个自然边界之后开始，避免从半句话起始。
        last_content_index = len(suffix.rstrip()) - 1
        boundaries = [
            index
            for index, character in enumerate(suffix)
            if character in _SENTENCE_ENDINGS and index < last_content_index
        ]
        boundary = min(boundaries, default=-1)
        return suffix[boundary + 1 :].strip() if boundary >= 0 else suffix.strip()


def _stable_chunk_id(document_id: str, chunk_index: int, content: str) -> str:
    value = f"{document_id}\0{chunk_index}\0{content}"
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]
    return f"chunk-{digest}"

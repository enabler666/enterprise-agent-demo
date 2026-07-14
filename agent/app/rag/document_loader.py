"""Markdown 业务文档加载器。"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from app.rag.models import KnowledgeDocument

_LEVEL_ONE_HEADING = re.compile(r"^#(?!#)\s+(.+?)\s*#*\s*$")


class DocumentLoadError(Exception):
    """知识文档无法按约定读取时抛出的异常。"""


class MarkdownDocumentLoader:
    """递归、稳定地加载知识库根目录中的非空 Markdown 文件。"""

    def __init__(self, knowledge_root: Path) -> None:
        self._knowledge_root = knowledge_root.resolve()

    def load(self) -> list[KnowledgeDocument]:
        """加载全部 Markdown 文档，结果按相对来源路径排序。"""
        if not self._knowledge_root.is_dir():
            raise DocumentLoadError(f"知识库目录不存在或不是目录：{self._knowledge_root}")

        paths = sorted(
            (
                path
                for path in self._knowledge_root.rglob("*")
                if path.is_file() and path.suffix.lower() == ".md"
            ),
            key=lambda path: path.relative_to(self._knowledge_root).as_posix(),
        )
        documents: list[KnowledgeDocument] = []
        for path in paths:
            source = path.relative_to(self._knowledge_root).as_posix()
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                raise DocumentLoadError(f"无法读取 Markdown 文档：{source}") from exc

            if not content.strip():
                continue
            documents.append(
                KnowledgeDocument(
                    id=_stable_document_id(source),
                    title=_extract_title(content, path.stem),
                    source=source,
                    content=content,
                )
            )
        return documents


def _extract_title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        match = _LEVEL_ONE_HEADING.match(line.strip())
        if match:
            return match.group(1).strip()
    return fallback


def _stable_document_id(source: str) -> str:
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:20]
    return f"doc-{digest}"

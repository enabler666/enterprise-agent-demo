"""开发人员预览 Markdown 知识文档切分结果的独立命令。"""

from __future__ import annotations

import os
from pathlib import Path

from app.rag.document_loader import MarkdownDocumentLoader
from app.rag.text_splitter import MarkdownTextSplitter

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_KNOWLEDGE_ROOT = _REPOSITORY_ROOT / "knowledge"


def main() -> None:
    """加载知识库并将全部文本块打印到标准输出。"""
    configured_root = os.environ.get("KNOWLEDGE_ROOT")
    knowledge_root = (
        Path(configured_root).expanduser() if configured_root else _DEFAULT_KNOWLEDGE_ROOT
    )
    documents = MarkdownDocumentLoader(knowledge_root).load()
    chunks = MarkdownTextSplitter().split_all(documents)

    print(f"知识库目录：{knowledge_root.resolve()}")
    print(f"加载文档数量：{len(documents)}")
    print(f"生成文本块数量：{len(chunks)}")
    for chunk in chunks:
        print("\n" + "=" * 80)
        print(f"块标识：{chunk.id}")
        print(f"文档标题：{chunk.document_title}")
        print(f"来源文件：{chunk.source}")
        print(f"块序号：{chunk.chunk_index}")
        print("-" * 80)
        print(chunk.content)


if __name__ == "__main__":
    main()

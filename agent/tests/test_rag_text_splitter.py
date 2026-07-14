from app.rag.models import KnowledgeDocument
from app.rag.text_splitter import MarkdownTextSplitter


def test_preserves_document_metadata_and_produces_no_empty_chunks() -> None:
    document = make_document("# 提报规则\n\n提交后进入统筹。\n\n## 修改\n\n未提交前可以修改。")

    chunks = MarkdownTextSplitter(chunk_size=30, chunk_overlap=5).split(document)

    assert chunks
    assert all(chunk.content.strip() for chunk in chunks)
    assert all(chunk.document_id == document.id for chunk in chunks)
    assert all(chunk.source == document.source for chunk in chunks)
    assert all(chunk.document_title == document.title for chunk in chunks)
    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))


def test_splits_long_content_without_losing_key_business_content() -> None:
    sections = [f"## 规则{i}\n\n第{i}项业务规则要求提交完整材料。" for i in range(30)]
    document = make_document("# 流转说明\n\n" + "\n\n".join(sections))

    chunks = MarkdownTextSplitter(chunk_size=120, chunk_overlap=20).split(document)
    combined = "\n".join(chunk.content for chunk in chunks)

    assert len(chunks) > 1
    assert "第0项业务规则要求提交完整材料" in combined
    assert "第29项业务规则要求提交完整材料" in combined


def test_long_paragraph_prefers_sentence_boundaries_and_keeps_order() -> None:
    content = "".join(f"第{i}条规则必须保留。" for i in range(40))
    document = make_document(content)

    chunks = MarkdownTextSplitter(chunk_size=80, chunk_overlap=10).split(document)
    first_positions = [content.find(f"第{i * 5}条规则") for i in range(8)]
    combined = "".join(chunk.content for chunk in chunks)

    assert len(chunks) > 1
    assert first_positions == sorted(first_positions)
    assert all(f"第{i}条规则必须保留" in combined for i in range(40))


def test_chunk_ids_and_order_are_stable_for_same_input() -> None:
    document = make_document("\n\n".join(f"第{i}段业务内容。" for i in range(20)))
    splitter = MarkdownTextSplitter(chunk_size=60, chunk_overlap=10)

    first = splitter.split(document)
    second = splitter.split(document)

    assert [chunk.id for chunk in first] == [chunk.id for chunk in second]
    assert [chunk.content for chunk in first] == [chunk.content for chunk in second]


def test_adjacent_paragraph_chunks_keep_boundary_overlap() -> None:
    document = make_document("第一段包含需要延续的上下文信息。\n\n第二段是新的业务规则内容。")

    chunks = MarkdownTextSplitter(chunk_size=20, chunk_overlap=10).split(document)

    assert len(chunks) == 2
    assert "上下文信息" in chunks[1].content


def test_split_all_preserves_document_order() -> None:
    first = make_document("第一篇内容", document_id="doc-first", source="first.md")
    second = make_document("第二篇内容", document_id="doc-second", source="second.md")

    chunks = MarkdownTextSplitter().split_all([first, second])

    assert [chunk.document_id for chunk in chunks] == ["doc-first", "doc-second"]


def make_document(
    content: str,
    document_id: str = "doc-stable",
    source: str = "rules/example.md",
) -> KnowledgeDocument:
    return KnowledgeDocument(
        id=document_id,
        title="业务规则",
        source=source,
        content=content,
    )

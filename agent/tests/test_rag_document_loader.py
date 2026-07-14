from pathlib import Path

from app.rag.document_loader import MarkdownDocumentLoader


def test_loads_markdown_files_in_stable_order_and_ignores_other_files(tmp_path: Path) -> None:
    write_text(tmp_path / "z-last.md", "# 最后文档\n\n最后内容")
    write_text(tmp_path / "nested" / "a-first.md", "# 第一文档\n\n第一内容")
    write_text(tmp_path / "ignored.txt", "不应加载")

    documents = MarkdownDocumentLoader(tmp_path).load()

    assert [document.source for document in documents] == ["nested/a-first.md", "z-last.md"]
    assert [document.title for document in documents] == ["第一文档", "最后文档"]


def test_uses_filename_when_level_one_heading_is_missing(tmp_path: Path) -> None:
    write_text(tmp_path / "业务规则.md", "## 二级标题\n\n规则正文")

    [document] = MarkdownDocumentLoader(tmp_path).load()

    assert document.title == "业务规则"
    assert document.id == MarkdownDocumentLoader(tmp_path).load()[0].id


def test_skips_empty_and_whitespace_only_files(tmp_path: Path) -> None:
    write_text(tmp_path / "empty.md", "")
    write_text(tmp_path / "blank.md", " \n\t")
    write_text(tmp_path / "valid.md", "有效内容")

    documents = MarkdownDocumentLoader(tmp_path).load()

    assert [document.source for document in documents] == ["valid.md"]


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

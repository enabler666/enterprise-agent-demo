"""本地 Chroma 检索预览命令，不调用大语言模型。"""

from __future__ import annotations

import argparse
import asyncio

from app.core.config import Settings
from app.rag.embedding import SiliconFlowEmbeddingProvider
from app.rag.retriever import KnowledgeRetriever
from app.rag.vector_store import ChromaVectorStore


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="预览业务知识库相似度检索结果")
    parser.add_argument("query", help="待检索的业务问题")
    parser.add_argument("--top-k", type=int, default=3, help="返回结果数量，默认 3")
    return parser.parse_args()


async def _run(query: str, top_k: int) -> None:
    settings = Settings.from_environment()
    if settings.siliconflow_api_key is None:
        raise RuntimeError("缺少 SILICONFLOW_API_KEY，无法生成查询向量。")
    store = ChromaVectorStore(
        settings.chroma_persist_directory, settings.chroma_collection_name
    )
    async with SiliconFlowEmbeddingProvider(
        settings.siliconflow_api_key,
        str(settings.siliconflow_base_url),
        settings.siliconflow_embedding_model,
    ) as provider:
        results = await KnowledgeRetriever(provider, store).retrieve(query, top_k)

    print(f"查询文本：{query}")
    print(f"Embedding 模型：{settings.siliconflow_embedding_model}")
    print(f"collection：{settings.chroma_collection_name}")
    for rank, result in enumerate(results, start=1):
        print("\n" + "=" * 80)
        print(f"排序：{rank}")
        print(f"distance：{result.distance}")
        print(f"文档标题：{result.document_title}")
        print(f"来源文件：{result.source}")
        print(f"chunk index：{result.chunk_index}")
        print("-" * 80)
        print(result.content)


def main() -> None:
    args = _parse_args()
    asyncio.run(_run(args.query, args.top_k))


if __name__ == "__main__":
    main()

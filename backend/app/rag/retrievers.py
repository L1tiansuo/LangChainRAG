"""ChromaDB-based semantic retriever for RAG."""

import logging

from app.core.chroma_client import get_kb_collection
from app.services.embedding_service import embed_text

logger = logging.getLogger("rag_kb")


async def retrieve_similar_chunks(
    query: str,
    top_k: int = 6,
) -> list[dict]:
    """Retrieve the most similar chunks from ChromaDB using dense vector search.

    Args:
        query: user's question text
        top_k: number of chunks to retrieve

    Returns:
        List of {"content": str, "metadata": dict, "score": float}
    """
    # Embed the query
    query_vector = await embed_text(query)

    # Search ChromaDB
    collection = get_kb_collection()
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
    )

    chunks = []
    if results["ids"] and results["ids"][0]:
        for i, chunk_id in enumerate(results["ids"][0]):
            chunks.append(
                {
                    "id": chunk_id,
                    "content": results["documents"][0][i] if results["documents"] else "",
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "score": results["distances"][0][i] if results["distances"] else 0.0,
                }
            )

    return chunks


async def retrieve_with_keyword_boost(
    query: str,
    keyword: str | None = None,
    top_k: int = 10,
) -> list[dict]:
    """Retrieve chunks with optional metadata filtering by keyword.

    Uses ChromaDB's where filter for keyword matching.
    """
    query_vector = await embed_text(query)
    collection = get_kb_collection()

    where_filter = None
    if keyword:
        # Filter chunks where content or source_file contains the keyword
        where_filter = {"$or": [
            {"source_file": {"$contains": keyword}},
            {"section_title": {"$contains": keyword}},
        ]}

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        where=where_filter,
    )

    chunks = []
    if results["ids"] and results["ids"][0]:
        for i, chunk_id in enumerate(results["ids"][0]):
            chunks.append(
                {
                    "id": chunk_id,
                    "content": results["documents"][0][i] if results["documents"] else "",
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "score": results["distances"][0][i] if results["distances"] else 0.0,
                }
            )

    return chunks

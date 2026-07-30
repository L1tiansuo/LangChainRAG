"""Batch loader: writes chunks to ChromaDB and SQLite."""

import json
import logging
import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.chroma_client import get_kb_collection
from app.models.document import Chunk

logger = logging.getLogger("rag_kb")


async def load_chunks_to_store(
    db: AsyncSession,
    document_id: str,
    chunks: list[dict],
    vectors: list[list[float]],
) -> int:
    """Load chunks, vectors, and metadata into ChromaDB + SQLite.

    Args:
        db: async database session
        document_id: parent document UUID
        chunks: list of {"content": str, "metadata": dict}
        vectors: list of embedding vectors (same length as chunks)

    Returns:
        Number of chunks loaded.
    """
    if not chunks or len(chunks) != len(vectors):
        raise ValueError("Chunks and vectors must be non-empty and same length")

    collection = get_kb_collection()

    # Prepare data for ChromaDB
    chroma_ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []
    embeddings: list[list[float]] = []

    for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
        chunk_id = str(uuid.uuid4())
        chroma_ids.append(chunk_id)
        documents.append(chunk["content"])
        metadata = {
            "chunk_id": chunk_id,
            "document_id": document_id,
            "source_file": chunk["metadata"].get("source_file", ""),
            "page_number": str(chunk["metadata"].get("page_number", "")),
            "section_title": chunk["metadata"].get("section_title", ""),
            "chunk_type": chunk["metadata"].get("chunk_type", "paragraph"),
            "chunk_index": i,
        }
        # Add any extra metadata (flatten string values for ChromaDB)
        for k, v in chunk["metadata"].items():
            if k not in metadata and v is not None:
                metadata[k] = str(v)
        metadatas.append(metadata)
        embeddings.append(vector)

    # Insert into ChromaDB
    try:
        collection.add(
            ids=chroma_ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )
    except Exception as e:
        logger.error(f"ChromaDB insert error: {e}")
        raise

    # Insert into SQLite chunks table
    for i, chunk in enumerate(chunks):
        db_chunk = Chunk(
            chroma_id=chroma_ids[i],
            document_id=document_id,
            chunk_index=i,
            chunk_type=chunk["metadata"].get("chunk_type", "paragraph"),
            content_preview=chunk["content"][:500],
            chunk_metadata=json.dumps(chunk["metadata"], ensure_ascii=False),
            token_count=None,
        )
        db.add(db_chunk)

    await db.flush()
    return len(chunks)

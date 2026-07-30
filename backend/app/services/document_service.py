"""Document processing service: orchestrates parsing → cleaning → chunking → embedding → storage."""

import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import async_session_factory
from app.ingestion.cleaner import clean_text
from app.ingestion.loader import load_chunks_to_store
from app.ingestion.parser import parse_document
from app.models.document import Document
from app.rag.chunking import chunk_document_pages
from app.services.embedding_service import embed_texts

logger = logging.getLogger("rag_kb")


async def process_document_bg(document_id: str) -> None:
    """Background task: full document ingestion pipeline.

    Parse → Clean → Chunk → Embed → Load into ChromaDB + SQLite.
    """
    async with async_session_factory() as db:
        try:
            # Fetch document record
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            doc = result.scalar_one_or_none()
            if not doc:
                logger.error(f"Document {document_id} not found")
                return

            file_path = doc.file_path
            if not file_path or not Path(file_path).exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Step 1: Parse
            logger.info(f"Parsing document {doc.original_name}...")
            doc.status = "parsing"
            await db.commit()

            parsed_docs = parse_document(file_path, doc.file_type)
            if not parsed_docs:
                raise ValueError("No text extracted from document")

            # Step 2: Clean
            pages = []
            for pd in parsed_docs:
                cleaned = clean_text(pd.text)
                if cleaned:
                    pages.append({"text": cleaned, "metadata": pd.metadata})

            if not pages:
                raise ValueError("No valid text after cleaning")

            # Step 3: Chunk
            logger.info(f"Chunking {len(pages)} sections...")
            doc.status = "chunking"
            await db.commit()

            # Use structured chunking for CSV, recursive for others
            if doc.file_type == "csv":
                all_chunks = chunk_document_pages(
                    pages, doc.original_name, chunk_size=300, chunk_overlap=50
                )
            else:
                all_chunks = chunk_document_pages(
                    pages, doc.original_name, chunk_size=500, chunk_overlap=80
                )

            if not all_chunks:
                raise ValueError("No chunks generated")

            # Step 4: Embed
            logger.info(f"Embedding {len(all_chunks)} chunks...")
            doc.status = "embedding"
            await db.commit()

            chunk_texts = [c["content"] for c in all_chunks]
            vectors = await embed_texts(chunk_texts)

            # Step 5: Load into stores
            logger.info(f"Loading {len(all_chunks)} chunks into vector store...")
            loaded_count = await load_chunks_to_store(
                db, document_id, all_chunks, vectors
            )

            # Mark as ready
            doc.status = "ready"
            doc.chunk_count = loaded_count
            await db.commit()

            logger.info(
                f"Document {doc.original_name} processed: {loaded_count} chunks"
            )

        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            # Update status to failed
            try:
                result = await db.execute(
                    select(Document).where(Document.id == document_id)
                )
                doc = result.scalar_one_or_none()
                if doc:
                    doc.status = "failed"
                    doc.error_message = str(e)
                    await db.commit()
            except Exception as inner_e:
                logger.error(f"Failed to update document status: {inner_e}")

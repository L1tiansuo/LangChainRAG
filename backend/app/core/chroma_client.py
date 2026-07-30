"""ChromaDB PersistentClient initialization."""

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings


_chroma_client: chromadb.PersistentClient | None = None
_kb_collection: chromadb.Collection | None = None


def get_chroma_client() -> chromadb.PersistentClient:
    """Get or create the ChromaDB PersistentClient (singleton)."""
    global _chroma_client
    if _chroma_client is None:
        persist_dir = settings.resolve_path(settings.CHROMA_PERSIST_DIR)
        persist_dir.mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _chroma_client


def get_kb_collection() -> chromadb.Collection:
    """Get or create the knowledge base collection."""
    global _kb_collection
    if _kb_collection is None:
        client = get_chroma_client()
        _kb_collection = client.get_or_create_collection(
            name="kb_chunks",
            metadata={
                "description": "RAG Knowledge Base - E-commerce Product Chunks",
                "hnsw:space": "cosine",
                "hnsw:construction_ef": 200,
                "hnsw:M": 16,
            },
        )
    return _kb_collection

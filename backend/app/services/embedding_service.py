"""Embedding service: DashScope text-embedding-v4 API wrapper with caching."""

import logging

from openai import AsyncOpenAI

from app.config import settings
from app.services.cache_service import get_embed_cache, set_embed_cache

logger = logging.getLogger("rag_kb")

_client: AsyncOpenAI | None = None


def get_embedding_client() -> AsyncOpenAI:
    """Get or create the OpenAI-compatible client for DashScope."""
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.DASHSCOPE_API_KEY,
            base_url=settings.DASHSCOPE_BASE_URL,
        )
    return _client


async def embed_text(text: str) -> list[float]:
    """Generate embedding for a single text with caching."""
    # Check cache
    cached = get_embed_cache(text)
    if cached is not None:
        return cached

    client = get_embedding_client()
    try:
        response = await client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text,
            dimensions=settings.EMBEDDING_DIMENSIONS,
        )
        vector = response.data[0].embedding
        set_embed_cache(text, vector)
        return vector
    except Exception as e:
        logger.error(f"Embedding API error: {e}")
        raise


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts in batches."""
    if not texts:
        return []

    vectors: list[list[float]] = []
    uncached_texts: list[tuple[int, str]] = []

    # Check cache first
    for i, text in enumerate(texts):
        cached = get_embed_cache(text)
        if cached is not None:
            vectors.append(cached)
        else:
            uncached_texts.append((i, text))
            vectors.append([])  # placeholder

    if not uncached_texts:
        return vectors

    # Batch call API (max 10 per batch for text-embedding-v4)
    client = get_embedding_client()
    batch_size = 10

    for start in range(0, len(uncached_texts), batch_size):
        batch = uncached_texts[start : start + batch_size]
        batch_texts = [t for _, t in batch]
        batch_indices = [i for i, _ in batch]

        try:
            response = await client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=batch_texts,
                dimensions=settings.EMBEDDING_DIMENSIONS,
            )
            for j, data in enumerate(response.data):
                vector = data.embedding
                idx = batch_indices[j]
                original_text = batch_texts[j]
                vectors[idx] = vector
                set_embed_cache(original_text, vector)

        except Exception as e:
            logger.error(f"Batch embedding error at {start}: {e}")
            # Fill failed slots with empty vectors
            for idx in batch_indices:
                vectors[idx] = [0.0] * settings.EMBEDDING_DIMENSIONS

    return vectors

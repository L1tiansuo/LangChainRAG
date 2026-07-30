"""Cache service: in-memory cachetools with optional Redis backend."""

import json
import hashlib
from cachetools import TTLCache

from app.config import settings

# In-memory caches
_embed_cache: TTLCache = TTLCache(maxsize=10000, ttl=86400)  # 24h
_rerank_cache: TTLCache = TTLCache(maxsize=5000, ttl=21600)  # 6h
_query_cache: TTLCache = TTLCache(maxsize=1000, ttl=1800)  # 30min


def _make_key(prefix: str, content: str) -> str:
    """Generate a cache key."""
    return f"{prefix}:{hashlib.md5(content.encode()).hexdigest()[:16]}"


def get_embed_cache(text: str) -> list[float] | None:
    """Get cached embedding vector for text."""
    key = _make_key("embed", text)
    result = _embed_cache.get(key)
    if result is not None:
        return json.loads(result) if isinstance(result, str) else result
    return None


def set_embed_cache(text: str, vector: list[float]) -> None:
    """Cache an embedding vector."""
    key = _make_key("embed", text)
    _embed_cache[key] = json.dumps(vector)


def get_rerank_cache(query: str, docs_key: str) -> list[dict] | None:
    """Get cached reranking result."""
    key = _make_key("rerank", f"{query}|{docs_key}")
    result = _rerank_cache.get(key)
    if result is not None:
        return json.loads(result) if isinstance(result, str) else result
    return None


def set_rerank_cache(query: str, docs_key: str, result: list[dict]) -> None:
    """Cache a reranking result."""
    key = _make_key("rerank", f"{query}|{docs_key}")
    _rerank_cache[key] = json.dumps(result)


def get_query_cache(query: str) -> dict | None:
    """Get cached query result."""
    key = _make_key("query", query.lower().strip())
    result = _query_cache.get(key)
    if result is not None:
        return json.loads(result) if isinstance(result, str) else result
    return None


def set_query_cache(query: str, result: dict) -> None:
    """Cache a query result."""
    key = _make_key("query", query.lower().strip())
    _query_cache[key] = json.dumps(result, ensure_ascii=False)

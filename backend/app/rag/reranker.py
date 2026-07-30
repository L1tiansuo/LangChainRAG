"""LLM-based chunk reranking for improved retrieval precision.

Uses a lightweight LLM call to score relevance of each candidate chunk.
"""

import json
import logging
import re

from app.config import settings
from app.services.cache_service import get_rerank_cache, set_rerank_cache
from app.services.llm_service import generate_complete

logger = logging.getLogger("rag_kb")

RERANK_PROMPT = """你是一个搜索相关性评分助手。请评估以下文档片段与用户问题的相关性，给出 1-10 的评分（10 表示高度相关）。

用户问题：{query}

文档片段：
{chunks}

请输出 JSON 格式的评分结果：
{{"scores": [{{"index": 0, "score": 8, "reason": "..."}}, ...]}}"""


def _parse_rerank_response(response: str, count: int) -> list[dict]:
    """Parse the LLM reranking response into scored results."""
    try:
        # Try to extract JSON
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return data.get("scores", [])
    except (json.JSONDecodeError, KeyError):
        pass

    # Fallback: return original order
    return [
        {"index": i, "score": 5, "reason": "parsing failed"}
        for i in range(count)
    ]


async def rerank_chunks(
    query: str,
    chunks: list[dict],
    top_n: int = 5,
) -> list[dict]:
    """Re-rank candidate chunks using LLM-based scoring.

    Args:
        query: original user question
        chunks: candidate chunks from retrieval (max 10)
        top_n: number of top chunks to return

    Returns:
        Re-ranked list of chunks (truncated to top_n).
    """
    if len(chunks) <= top_n:
        return chunks

    # Check cache
    docs_key = "|".join(c.get("id", str(i)) for i, c in enumerate(chunks[:10]))
    cached = get_rerank_cache(query, docs_key)
    if cached is not None:
        # Apply cached ordering
        reordered = [chunks[r["index"]] for r in cached if r["index"] < len(chunks)]
        return reordered[:top_n]

    # Prepare chunks for scoring
    chunks_text = ""
    for i, chunk in enumerate(chunks[:10]):
        preview = chunk["content"][:300]
        chunks_text += f"[{i}] {preview}\n\n"

    prompt = RERANK_PROMPT.format(query=query, chunks=chunks_text)

    try:
        response = await generate_complete(
            system_prompt="你是一个搜索相关性评分助手，只输出 JSON 格式的结果。",
            user_prompt=prompt,
            model=settings.LLM_MODEL_LIGHT,  # Use cheapest model for reranking
            temperature=0.1,
            max_tokens=1000,
        )

        scores = _parse_rerank_response(response, len(chunks[:10]))

        # Cache the result
        set_rerank_cache(query, docs_key, scores)

        # Reorder and return top_n
        scored_chunks = []
        for s in scores:
            idx = s.get("index", 0)
            if idx < len(chunks):
                chunk = chunks[idx].copy()
                chunk["rerank_score"] = s.get("score", 0)
                scored_chunks.append(chunk)

        scored_chunks.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
        return scored_chunks[:top_n]

    except Exception as e:
        logger.warning(f"Reranking failed, using original order: {e}")
        return chunks[:top_n]

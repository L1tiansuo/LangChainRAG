"""Query rewriting strategies: HyDE and Multi-Query expansion."""

import logging

from app.rag.prompts import HYDE_PROMPT, MULTI_QUERY_PROMPT
from app.services.llm_service import generate_complete

logger = logging.getLogger("rag_kb")


async def hyde_rewrite(query: str) -> str:
    """Generate a hypothetical document using HyDE technique.

    The generated text is used for embedding-based retrieval
    instead of the original query, often improving recall for
    open-ended questions.
    """
    prompt = HYDE_PROMPT.format(question=query)
    try:
        hypothetical = await generate_complete(
            system_prompt="你是一个电商产品知识专家。",
            user_prompt=prompt,
            model="qwen-turbo",
            temperature=0.7,
            max_tokens=500,
        )
        return hypothetical.strip()
    except Exception as e:
        logger.warning(f"HyDE rewrite failed: {e}")
        return query


async def multi_query_rewrite(query: str) -> list[str]:
    """Generate multiple search queries from a single user question.

    Returns:
        List of rewritten query strings (original + 3 variants).
    """
    prompt = MULTI_QUERY_PROMPT.format(question=query)
    try:
        response = await generate_complete(
            system_prompt="你是一个搜索查询优化专家。",
            user_prompt=prompt,
            model="qwen-turbo",
            temperature=0.5,
            max_tokens=300,
        )

        # Parse response into individual queries
        lines = [line.strip() for line in response.strip().split("\n") if line.strip()]
        # Filter out numbering prefixes like "1." or "1、"
        queries = []
        for line in lines:
            # Remove leading numbers and punctuation
            cleaned = line.lstrip("0123456789.、) ").strip()
            if cleaned and cleaned != query:
                queries.append(cleaned)

        # Always include the original query
        if query not in queries:
            queries.insert(0, query)

        return queries[:4]  # max 4 queries

    except Exception as e:
        logger.warning(f"Multi-query rewrite failed: {e}")
        return [query]

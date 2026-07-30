"""LLM service: DashScope LLM wrapper with model tier routing."""

import logging
import re
from typing import AsyncIterator

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger("rag_kb")

_client: AsyncOpenAI | None = None


def get_llm_client() -> AsyncOpenAI:
    """Get or create the OpenAI-compatible client."""
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.DASHSCOPE_API_KEY,
            base_url=settings.DASHSCOPE_BASE_URL,
        )
    return _client


# Query complexity patterns for tier routing
SIMPLE_PATTERNS = [
    r"(多少[钱价])|(价格|价钱|售价|报价|多少钱)",
    r"(什么[是叫])|(定义|概念|名词解释)",
    r"(规格|参数|型号|尺寸|颜色|重量|材质)",
    r"\?$|吗\?$|吧\?$",
]

COMPLEX_PATTERNS = [
    r"(对比|比较|区别|差异|优劣|哪个更好)",
    r"(为什么|原因|分析|深度|详解)",
    r"(推荐|建议|方案|怎么[选择挑])",
]


def route_model(query: str) -> str:
    """Route query to appropriate LLM model tier."""
    for pattern in COMPLEX_PATTERNS:
        if re.search(pattern, query):
            return settings.LLM_MODEL_HEAVY  # qwen-max
    for pattern in SIMPLE_PATTERNS:
        if re.search(pattern, query):
            return settings.LLM_MODEL_LIGHT  # qwen-turbo
    return settings.LLM_MODEL_PRIMARY  # qwen-plus


async def generate_stream(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 2000,
) -> AsyncIterator[str]:
    """Generate a streaming response from the LLM.

    Args:
        system_prompt: system-level instructions
        user_prompt: the full user-facing prompt with context
        model: specific model override (auto-routed if None)
        temperature: generation temperature
        max_tokens: max output tokens

    Yields:
        Token strings as they arrive.
    """
    if model is None:
        # Auto-route based on query complexity
        model = route_model(user_prompt)

    logger.info(f"LLM call: model={model}, prompt_len={len(user_prompt)}")

    client = get_llm_client()
    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    except Exception as e:
        logger.error(f"LLM streaming error: {e}")
        raise


async def generate_complete(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 2000,
) -> str:
    """Generate a complete (non-streaming) response from the LLM."""
    if model is None:
        model = route_model(user_prompt)

    client = get_llm_client()
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    except Exception as e:
        logger.error(f"LLM generation error: {e}")
        raise

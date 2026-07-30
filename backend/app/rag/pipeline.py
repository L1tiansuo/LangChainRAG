"""RAG Pipeline assembly using LangChain LCEL concepts.

Core flow:
  Query → Retrieve → (optional Rerank) → Format Context → LLM Generate → Citation Extract
"""

from app.rag.prompts import QA_PROMPT_TEMPLATE, SYSTEM_PROMPT
from app.rag.retrievers import retrieve_similar_chunks


def format_context_for_prompt(
    chunks: list[dict],
    max_chunks: int = 5,
) -> str:
    """Format retrieved chunks as numbered references for the prompt.

    Args:
        chunks: list of {"content": str, "metadata": dict, "score": float}
        max_chunks: max number of chunks to include

    Returns:
        Formatted context string with numbered references.
    """
    top_chunks = chunks[:max_chunks]
    parts = []

    for i, chunk in enumerate(top_chunks, start=1):
        meta = chunk.get("metadata", {})
        source = meta.get("source_file", "未知来源")
        page = meta.get("page_number", "")
        section = meta.get("section_title", "")

        header = f"[{i}] 来源: {source}"
        if page:
            header += f", 页码: {page}"
        if section:
            header += f", 章节: {section}"

        parts.append(f"{header}\n内容: {chunk['content']}")

    return "\n\n".join(parts)


def extract_citations_from_chunks(
    chunks: list[dict],
    answer_text: str,
) -> list[dict]:
    """Extract source citations from retrieved chunks.

    Args:
        chunks: retrieved chunks with metadata
        answer_text: generated answer (to match citation markers)

    Returns:
        List of citation objects.
    """
    citations = []
    seen_sources = set()

    for i, chunk in enumerate(chunks[:5], start=1):
        meta = chunk.get("metadata", {})
        source = meta.get("source_file", "未知来源")

        # Only include if referenced in the answer
        if f"[{i}]" in answer_text:
            source_key = f"{source}:{meta.get('page_number', '')}"
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                citations.append(
                    {
                        "id": i,
                        "file": source,
                        "page": int(meta.get("page_number", 0))
                        if meta.get("page_number")
                        else 0,
                        "snippet": chunk["content"][:200],
                        "section": meta.get("section_title", ""),
                    }
                )

    return citations


async def run_rag_pipeline(
    query: str,
    top_k: int = 6,
    context_max_chunks: int = 5,
) -> dict:
    """Run the complete RAG pipeline.

    Args:
        query: user's question
        top_k: number of chunks to retrieve
        context_max_chunks: chunks to include in prompt

    Returns:
        {
            "chunks": list of retrieved chunks,
            "context_text": formatted context string,
            "prompt": assembled user prompt,
            "system_prompt": system prompt,
        }
    """
    # Stage 1: Retrieve
    chunks = await retrieve_similar_chunks(query, top_k=top_k)

    # Stage 2: Format context
    context_text = format_context_for_prompt(chunks, max_chunks=context_max_chunks)

    # Stage 3: Assemble prompt
    user_prompt = QA_PROMPT_TEMPLATE.format(
        system_prompt=SYSTEM_PROMPT,
        context=context_text,
        question=query,
    )

    return {
        "chunks": chunks,
        "context_text": context_text,
        "prompt": user_prompt,
        "system_prompt": SYSTEM_PROMPT,
    }

"""Conversation memory management.

Dual memory system:
  - Short-term: last N messages kept as-is
  - Long-term: running summary for sessions exceeding N messages
"""

from langchain.memory import ConversationBufferWindowMemory, ConversationSummaryMemory

from app.rag.prompts import SUMMARY_PROMPT
from app.services.llm_service import generate_complete


def create_buffer_memory(k: int = 6) -> ConversationBufferWindowMemory:
    """Create a short-term buffer memory keeping the last k messages."""
    return ConversationBufferWindowMemory(
        k=k,
        return_messages=True,
        memory_key="chat_history",
    )


async def summarize_history(messages: list[dict]) -> str:
    """Generate a concise summary of conversation history.

    Args:
        messages: list of {"role": str, "content": str}

    Returns:
        Summary string (Chinese).
    """
    # Build chat history text
    history_lines = []
    for msg in messages[-20:]:  # last 20 messages max
        role = "用户" if msg["role"] == "user" else "助手"
        history_lines.append(f"{role}: {msg['content']}")

    chat_history = "\n".join(history_lines)
    prompt = SUMMARY_PROMPT.format(chat_history=chat_history)

    try:
        summary = await generate_complete(
            system_prompt="你是一个对话摘要助手，请简洁地总结以下对话。",
            user_prompt=prompt,
            model="qwen-turbo",
            temperature=0.3,
            max_tokens=200,
        )
        return summary.strip()
    except Exception:
        # Fallback: use last user message as summary
        for msg in reversed(messages):
            if msg["role"] == "user":
                return msg["content"][:200]
        return ""


def format_chat_history_for_prompt(
    recent_messages: list[dict],
    summary: str | None = None,
    max_messages: int = 6,
) -> str:
    """Format recent messages + optional summary for the RAG prompt.

    Args:
        recent_messages: recent messages from this session
        summary: long-term summary (if available)
        max_messages: max recent messages to include

    Returns:
        Formatted string for inclusion in the prompt.
    """
    parts = []

    if summary:
        parts.append(f"## 对话历史摘要\n{summary}")

    if recent_messages:
        history = []
        for msg in recent_messages[-max_messages:]:
            role = "用户" if msg["role"] == "user" else "助手"
            content = msg["content"]
            if len(content) > 500:
                content = content[:500] + "..."
            history.append(f"{role}: {content}")
        parts.append("## 近期对话\n" + "\n".join(history))

    return "\n\n".join(parts)

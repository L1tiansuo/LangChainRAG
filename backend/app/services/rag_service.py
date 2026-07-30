"""RAG orchestration service with SSE streaming support."""

import json
import logging
import time
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models.message import Message
from app.models.session import Session
from app.rag.pipeline import extract_citations_from_chunks, run_rag_pipeline
from app.services.llm_service import generate_stream

logger = logging.getLogger("rag_kb")


class SSEEventBuilder:
    """Helper to build SSE event strings."""

    @staticmethod
    def event(event_type: str, data: dict | list | str) -> str:
        if isinstance(data, (dict, list)):
            data = json.dumps(data, ensure_ascii=False)
        return f"event: {event_type}\ndata: {data}\n\n"

    @staticmethod
    def thinking(stage: str) -> str:
        return SSEEventBuilder.event("thinking", {"stage": stage})

    @staticmethod
    def token(t: str) -> str:
        return SSEEventBuilder.event("token", {"token": t})

    @staticmethod
    def sources(s: list) -> str:
        return SSEEventBuilder.event("sources", s)

    @staticmethod
    def done(message_id: str, tokens_used: int, latency_ms: int) -> str:
        return SSEEventBuilder.event("done", {
            "message_id": message_id,
            "tokens_used": tokens_used,
            "latency_ms": latency_ms,
        })

    @staticmethod
    def error(message: str) -> str:
        return SSEEventBuilder.event("error", {"message": message})


async def execute_rag_query(
    session_id: str,
    user_id: str,
    question: str,
) -> str:
    """Execute a RAG query with SSE streaming.

    Yields SSE event strings.
    """
    evt = SSEEventBuilder()
    start_time = time.time()

    # Yield thinking: retrieving
    yield evt.thinking("retrieving")

    try:
        # Run RAG pipeline
        pipeline_result = await run_rag_pipeline(question)

        chunks = pipeline_result["chunks"]
        if not chunks:
            yield evt.thinking("generating")
            yield evt.token("根据现有资料，我无法回答这个问题，建议您联系客服获取更多信息。")
            yield evt.sources([])

            latency_ms = int((time.time() - start_time) * 1000)
            # Save messages
            msg_id = await save_chat_messages(
                session_id, user_id, question,
                "根据现有资料，我无法回答这个问题，建议您联系客服获取更多信息。",
                [], latency_ms,
            )
            yield evt.done(msg_id, 0, latency_ms)
            return

        # Yield thinking: generating
        yield evt.thinking("generating")

        # Generate answer via LLM
        full_answer = ""
        token_count = 0

        async for token in generate_stream(
            system_prompt=pipeline_result["system_prompt"],
            user_prompt=pipeline_result["prompt"],
        ):
            full_answer += token
            token_count += 1
            yield evt.token(token)

        # Extract and yield citations
        citations = extract_citations_from_chunks(chunks, full_answer)
        yield evt.sources(citations)

        latency_ms = int((time.time() - start_time) * 1000)

        # Save messages to database
        msg_id = await save_chat_messages(
            session_id, user_id, question,
            full_answer, citations, latency_ms,
        )

        yield evt.done(msg_id, token_count, latency_ms)

    except Exception as e:
        logger.error(f"RAG query error: {e}")
        yield evt.error(str(e))


async def save_chat_messages(
    session_id: str,
    user_id: str,
    question: str,
    answer: str,
    citations: list[dict],
    latency_ms: int,
) -> str:
    """Save user message and assistant response to the database."""
    async with async_session_factory() as db:
        try:
            # Save user message
            user_msg = Message(
                session_id=session_id,
                role="user",
                content=question,
            )
            db.add(user_msg)
            await db.flush()

            # Save assistant message
            assistant_msg = Message(
                session_id=session_id,
                role="assistant",
                content=answer,
                citations=json.dumps(citations, ensure_ascii=False) if citations else None,
                latency_ms=latency_ms,
            )
            db.add(assistant_msg)
            await db.flush()

            # Update session metadata
            result = await db.execute(select(Session).where(Session.id == session_id))
            session = result.scalar_one_or_none()
            if session:
                # Auto-generate title from first question
                if session.message_count == 0:
                    session.title = question[:30] + ("..." if len(question) > 30 else "")

                session.message_count = (session.message_count or 0) + 2
                session.updated_at = datetime.now(timezone.utc)

            await db.commit()
            return assistant_msg.id

        except Exception as e:
            logger.error(f"Failed to save messages: {e}")
            await db.rollback()
            raise

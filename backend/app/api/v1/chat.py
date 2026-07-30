"""Chat / Q&A API routes (SSE streaming)."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppError, raise_app_error
from app.middleware.auth import get_current_user
from app.models.session import Session
from app.models.user import User
from app.services.rag_service import execute_rag_query

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


class ChatQueryRequest(BaseModel):
    session_id: str
    message: str


@router.post("/query")
async def chat_query(
    body: ChatQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a question and receive a streaming RAG answer (SSE)."""
    # Verify session ownership
    result = await db.execute(
        select(Session).where(
            Session.id == body.session_id,
            Session.user_id == current_user.id,
            Session.status != "deleted",
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise_app_error(AppError.SESSION_NOT_FOUND, 404)

    return StreamingResponse(
        execute_rag_query(body.session_id, current_user.id, body.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

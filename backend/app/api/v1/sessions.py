"""Session management API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppError, raise_app_error
from app.middleware.auth import get_current_user
from app.models.message import Message
from app.models.session import Session
from app.models.user import User
from app.schemas.chat import MessageListResponse, MessageResponse
from app.schemas.session import (
    SessionCreate,
    SessionListResponse,
    SessionResponse,
    SessionUpdate,
)

router = APIRouter(prefix="/api/v1/sessions", tags=["Sessions"])


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's sessions."""
    query = select(Session).where(
        Session.user_id == current_user.id,
        Session.status != "deleted",
    )
    if status:
        query = query.where(Session.status == status)
    query = query.order_by(Session.updated_at.desc())

    # Count total
    count_query = select(func.count()).select_from(Session).where(
        Session.user_id == current_user.id,
        Session.status != "deleted",
    )
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    sessions = result.scalars().all()

    return SessionListResponse(
        sessions=[SessionResponse.model_validate(s) for s in sessions],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(
    body: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new conversation session."""
    session = Session(user_id=current_user.id, title=body.title)
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return SessionResponse.model_validate(session)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get session details."""
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise_app_error(AppError.SESSION_NOT_FOUND, 404)
    return SessionResponse.model_validate(session)


@router.get("/{session_id}/messages", response_model=MessageListResponse)
async def get_messages(
    session_id: str,
    cursor: str | None = Query(None),
    limit: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get messages in a session (cursor-based pagination)."""
    # Verify ownership
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise_app_error(AppError.SESSION_NOT_FOUND, 404)

    query = select(Message).where(Message.session_id == session_id)
    if cursor:
        query = query.where(Message.id < cursor)
    query = query.order_by(Message.created_at.desc()).limit(limit + 1)

    result = await db.execute(query)
    messages = result.scalars().all()

    has_more = len(messages) > limit
    if has_more:
        messages = messages[:limit]

    # Return in chronological order
    messages = list(reversed(messages))

    return MessageListResponse(
        messages=[MessageResponse.model_validate(m) for m in messages],
        next_cursor=messages[0].id if messages and has_more else None,
        has_more=has_more,
    )


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    body: SessionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update session title or status."""
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise_app_error(AppError.SESSION_NOT_FOUND, 404)

    if body.title is not None:
        session.title = body.title
    if body.status is not None:
        session.status = body.status

    await db.flush()
    await db.refresh(session)
    return SessionResponse.model_validate(session)


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a session."""
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise_app_error(AppError.SESSION_NOT_FOUND, 404)

    session.status = "deleted"
    await db.flush()
    return {"message": "会话已删除"}

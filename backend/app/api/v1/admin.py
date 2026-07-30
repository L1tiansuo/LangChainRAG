"""Admin API routes (user management)."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppError, raise_app_error
from app.middleware.auth import get_admin_user
from app.models.user import User
from app.schemas.auth import UserInfo

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


class UserStatusUpdate(BaseModel):
    is_active: bool


@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: str | None = None,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List all users (admin only)."""
    query = select(User)
    count_query = select(func.count()).select_from(User)

    if role:
        query = query.where(User.role == role)
        count_query = count_query.where(User.role == role)

    query = query.order_by(User.created_at.desc())
    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    users = result.scalars().all()

    return {
        "users": [UserInfo.model_validate(u).model_dump() for u in users],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.patch("/users/{user_id}")
async def update_user_status(
    user_id: str,
    body: UserStatusUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Enable/disable a user account."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise_app_error(("USER_NOT_FOUND", "用户不存在"), 404)

    if user.id == current_user.id:
        raise_app_error(("CANNOT_DISABLE_SELF", "不能禁用自己的账户"), 400)

    user.is_active = body.is_active
    await db.flush()
    return {"message": "用户状态已更新", "user": UserInfo.model_validate(user).model_dump()}

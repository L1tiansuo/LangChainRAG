"""JWT authentication middleware / FastAPI dependency."""

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppError, raise_app_error
from app.core.security import decode_access_token
from app.models.user import User


async def get_current_user(
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency: validates JWT and returns current user."""
    if not authorization.startswith("Bearer "):
        raise_app_error(AppError.INVALID_TOKEN, 401)

    token = authorization.removeprefix("Bearer ")
    payload = decode_access_token(token)
    if payload is None:
        raise_app_error(AppError.TOKEN_EXPIRED, 401)

    user_id = payload.get("sub")
    if not user_id:
        raise_app_error(AppError.INVALID_TOKEN, 401)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise_app_error(AppError.INVALID_TOKEN, 401)

    if not user.is_active:
        raise_app_error(("ACCOUNT_DISABLED", "账户已被禁用"), 403)

    return user


async def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """FastAPI dependency: only allows admin users."""
    if current_user.role != "admin":
        raise_app_error(AppError.ADMIN_ONLY, 403)
    return current_user

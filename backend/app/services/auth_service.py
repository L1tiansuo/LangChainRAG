"""Authentication service: register, login, password management."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import AppError, raise_app_error
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import UserInfo


async def register_user(
    db: AsyncSession,
    username: str,
    password: str,
    email: str | None = None,
) -> User:
    """Register a new user."""
    existing = await db.execute(select(User).where(User.username == username))
    if existing.scalar_one_or_none():
        raise_app_error(AppError.USERNAME_EXISTS, 409)

    user = User(
        username=username,
        password_hash=hash_password(password),
        email=email,
        role="user",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def login_user(db: AsyncSession, username: str, password: str) -> dict:
    """Authenticate user and return JWT token."""
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        raise_app_error(AppError.INVALID_CREDENTIALS, 401)

    if not user.is_active:
        raise_app_error(("ACCOUNT_DISABLED", "账户已被禁用"), 403)

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    await db.flush()

    access_token = create_access_token(
        data={"sub": user.id, "role": user.role, "username": user.username}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_EXPIRE_MINUTES * 60,
        "user": UserInfo.model_validate(_user_to_dict(user)),
    }


async def change_password(
    db: AsyncSession,
    user: User,
    old_password: str,
    new_password: str,
) -> None:
    """Change user password."""
    if not verify_password(old_password, user.password_hash):
        raise_app_error(AppError.OLD_PASSWORD_WRONG, 400)

    user.password_hash = hash_password(new_password)
    await db.flush()


def _user_to_dict(user: User) -> dict:
    """Convert ORM User to dict with string datetimes."""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else "",
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
    }


def format_user_info(user: User) -> dict:
    """Format user object to info dict."""
    return UserInfo.model_validate(_user_to_dict(user)).model_dump()

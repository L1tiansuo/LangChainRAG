"""Pydantic schemas for authentication."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    email: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserInfo"


class UserInfo(BaseModel):
    id: str
    username: str
    email: str | None = None
    role: str
    is_active: bool
    created_at: str
    last_login_at: str | None = None

    model_config = {"from_attributes": True}

    @field_validator("created_at", "last_login_at", mode="before")
    @classmethod
    def coerce_datetime(cls, v: object) -> str | None:
        """Convert datetime objects to ISO format strings."""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v) if v else None

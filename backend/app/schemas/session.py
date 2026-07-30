"""Pydantic schemas for sessions."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class SessionCreate(BaseModel):
    title: str = "新会话"


class SessionUpdate(BaseModel):
    title: str | None = None
    status: str | None = None  # 'active' | 'archived' | 'deleted'


class SessionResponse(BaseModel):
    id: str
    user_id: str
    title: str
    status: str
    message_count: int
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def coerce_datetime(cls, v: object) -> str:
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v) if v else ""


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int
    page: int
    page_size: int

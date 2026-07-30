"""Pydantic schemas for chat/Q&A."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(..., min_length=1, max_length=5000)


class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    citations: str | None = None  # JSON string
    token_count: int | None = None
    latency_ms: int | None = None
    created_at: str

    model_config = {"from_attributes": True}

    @field_validator("created_at", mode="before")
    @classmethod
    def coerce_datetime(cls, v: object) -> str:
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v) if v else ""


class MessageListResponse(BaseModel):
    messages: list[MessageResponse]
    next_cursor: str | None = None
    has_more: bool = False

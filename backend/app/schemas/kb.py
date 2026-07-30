"""Pydantic schemas for knowledge base management."""

from datetime import datetime

from pydantic import BaseModel, field_validator


class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_name: str
    file_type: str
    file_size: int | None = None
    status: str
    chunk_count: int
    error_message: str | None = None
    uploaded_by: str | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def coerce_datetime(cls, v: object) -> str:
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v) if v else ""


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int
    page: int
    page_size: int


class ChunkResponse(BaseModel):
    id: str
    chroma_id: str
    document_id: str
    chunk_index: int
    chunk_type: str | None = None
    content_preview: str | None = None
    chunk_metadata: str | None = None
    token_count: int | None = None
    created_at: str

    model_config = {"from_attributes": True}

    @field_validator("created_at", mode="before")
    @classmethod
    def coerce_datetime(cls, v: object) -> str:
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v) if v else ""


class ChunkListResponse(BaseModel):
    chunks: list[ChunkResponse]
    total: int
    page: int
    page_size: int


class KBStatsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    total_storage_bytes: int
    documents_by_status: dict[str, int]
    documents_by_type: dict[str, int]

"""Knowledge Base management API routes (admin only)."""

import asyncio
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.core.exceptions import AppError, raise_app_error
from app.middleware.auth import get_admin_user
from app.models.document import Chunk, Document
from app.models.user import User
from app.schemas.kb import (
    ChunkListResponse,
    ChunkResponse,
    DocumentListResponse,
    DocumentResponse,
    KBStatsResponse,
)

router = APIRouter(prefix="/api/v1/kb", tags=["Knowledge Base"])

ALLOWED_TYPES = {"pdf", "docx", "csv", "txt", "md", "html"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    file_type: str | None = None,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List all knowledge base documents."""
    query = select(Document)
    count_query = select(func.count()).select_from(Document)

    if status:
        query = query.where(Document.status == status)
        count_query = count_query.where(Document.status == status)
    if file_type:
        query = query.where(Document.file_type == file_type)
        count_query = count_query.where(Document.file_type == file_type)

    query = query.order_by(Document.created_at.desc())
    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    documents = result.scalars().all()

    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in documents],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/documents/upload", status_code=202)
async def upload_document(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document for knowledge base ingestion."""
    if not file.filename:
        raise_app_error(("NO_FILENAME", "文件名为空"), 400)

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_TYPES:
        raise_app_error(AppError.UNSUPPORTED_TYPE, 400)

    # Read file content
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise_app_error(AppError.FILE_TOO_LARGE, 400)

    # Save file
    upload_dir = settings.resolve_path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4()}.{ext}"
    file_path = upload_dir / stored_name
    file_path.write_bytes(content)

    # Create document record
    doc = Document(
        filename=stored_name,
        original_name=file.filename,
        file_type=ext,
        file_size=len(content),
        file_path=str(file_path),
        status="uploading",
        uploaded_by=current_user.id,
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)
    await db.commit()  # Ensure document is visible to background task

    # Dispatch async processing via asyncio.create_task (more reliable than BackgroundTasks)
    from app.services.document_service import process_document_bg
    asyncio.create_task(process_document_bg(str(doc.id)))

    return {"document_id": doc.id, "filename": file.filename, "status": "uploading"}


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get document details."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise_app_error(AppError.DOCUMENT_NOT_FOUND, 404)
    return DocumentResponse.model_validate(doc)


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document and all its chunks."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise_app_error(AppError.DOCUMENT_NOT_FOUND, 404)

    # Remove from ChromaDB
    try:
        from app.core.chroma_client import get_kb_collection
        chunk_result = await db.execute(
            select(Chunk).where(Chunk.document_id == document_id)
        )
        chunks = chunk_result.scalars().all()
        chroma_ids = [c.chroma_id for c in chunks]
        if chroma_ids:
            collection = get_kb_collection()
            collection.delete(ids=chroma_ids)
    except Exception:
        pass  # Best-effort cleanup

    # Delete file
    if doc.file_path:
        try:
            Path(doc.file_path).unlink(missing_ok=True)
        except Exception:
            pass

    await db.delete(doc)
    await db.flush()
    return {"message": "文档已删除"}


@router.get("/chunks", response_model=ChunkListResponse)
async def list_chunks(
    document_id: str = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List chunks for a document."""
    query = select(Chunk).where(Chunk.document_id == document_id)
    count_query = select(func.count()).select_from(Chunk).where(Chunk.document_id == document_id)

    query = query.order_by(Chunk.chunk_index)
    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    chunks = result.scalars().all()

    return ChunkListResponse(
        chunks=[ChunkResponse.model_validate(c) for c in chunks],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/stats", response_model=KBStatsResponse)
async def get_kb_stats(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get knowledge base statistics."""
    # Total documents
    total_docs = (await db.execute(select(func.count()).select_from(Document))).scalar() or 0
    # Total chunks
    total_chunks = (await db.execute(select(func.count()).select_from(Chunk))).scalar() or 0
    # Total storage
    total_storage = (
        await db.execute(select(func.coalesce(func.sum(Document.file_size), 0)).select_from(Document))
    ).scalar() or 0

    # By status
    status_result = await db.execute(
        select(Document.status, func.count()).group_by(Document.status)
    )
    by_status = {row[0]: row[1] for row in status_result}

    # By type
    type_result = await db.execute(
        select(Document.file_type, func.count()).group_by(Document.file_type)
    )
    by_type = {row[0]: row[1] for row in type_result}

    return KBStatsResponse(
        total_documents=total_docs,
        total_chunks=total_chunks,
        total_storage_bytes=total_storage,
        documents_by_status=by_status,
        documents_by_type=by_type,
    )


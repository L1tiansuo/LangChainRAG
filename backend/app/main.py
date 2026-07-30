"""FastAPI application factory."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException

from app.api.router import api_router
from app.config import settings
from app.core.database import init_db
from app.core.exceptions import app_exception_handler, general_exception_handler
from app.middleware.cors import setup_cors
from app.middleware.logging import log_requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("rag_kb")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # Startup
    logger.info("Starting RAG Knowledge Base system...")

    # Ensure data directories exist
    for dir_path in ["data", settings.UPLOAD_DIR, settings.CHROMA_PERSIST_DIR]:
        path = settings.resolve_path(dir_path)
        path.mkdir(parents=True, exist_ok=True)

    # Initialize database tables
    await init_db()
    logger.info("Database tables ensured.")

    # Initialize ChromaDB
    try:
        from app.core.chroma_client import get_kb_collection
        get_kb_collection()
        logger.info("ChromaDB collection ready.")
    except Exception as e:
        logger.warning(f"ChromaDB init warning: {e}")

    yield

    # Shutdown
    logger.info("Shutting down RAG Knowledge Base system...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="RAG 企业知识库问答系统",
        description="基于 LangChain + 阿里云百炼的 RAG 知识库问答系统",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Setup CORS
    setup_cors(app)

    # Register middleware
    app.middleware("http")(log_requests)

    # Register exception handlers
    app.add_exception_handler(HTTPException, app_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # Register API routes
    app.include_router(api_router)

    # Health check
    @app.get("/health")
    async def health_check():
        return {"status": "ok", "version": "1.0.0"}

    return app


app = create_app()

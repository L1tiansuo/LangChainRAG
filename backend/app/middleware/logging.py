"""Request logging middleware."""

import logging
import time

from fastapi import FastAPI, Request

logger = logging.getLogger("rag_kb")


async def log_requests(request: Request, call_next):
    """Log each request with method, path, status, and duration."""
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    logger.info(
        "request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round(duration * 1000, 2),
        },
    )
    return response

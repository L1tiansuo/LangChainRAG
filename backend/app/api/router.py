"""Aggregate all API routers."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.sessions import router as sessions_router
from app.api.v1.chat import router as chat_router
from app.api.v1.kb import router as kb_router
from app.api.v1.admin import router as admin_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(sessions_router)
api_router.include_router(chat_router)
api_router.include_router(kb_router)
api_router.include_router(admin_router)

"""FastAPI dependency overrides and common dependencies."""

# Re-export for convenience
from app.core.database import get_db
from app.middleware.auth import get_current_user, get_admin_user

__all__ = ["get_db", "get_current_user", "get_admin_user"]

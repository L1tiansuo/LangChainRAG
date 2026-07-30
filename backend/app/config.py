"""Application configuration via Pydantic Settings."""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Project paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    # DashScope / Bailian
    DASHSCOPE_API_KEY: str
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///data/app.db"

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "data/chroma"

    # Upload
    UPLOAD_DIR: str = "uploads"

    # JWT
    JWT_SECRET_KEY: str = ""  # Must be set via .env — no insecure default
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24 hours

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 20

    # Model Configuration
    LLM_MODEL_PRIMARY: str = "qwen-plus"
    LLM_MODEL_LIGHT: str = "qwen-turbo"
    LLM_MODEL_HEAVY: str = "qwen-max"
    EMBEDDING_MODEL: str = "text-embedding-v4"
    EMBEDDING_DIMENSIONS: int = 1024

    # Optional Redis
    REDIS_URL: Optional[str] = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    def resolve_path(self, relative_path: str) -> Path:
        """Resolve a relative path against BASE_DIR."""
        return self.BASE_DIR / relative_path


settings = Settings()

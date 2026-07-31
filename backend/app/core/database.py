"""SQLAlchemy async engine and session factory.

SQLite optimizations for concurrent access:
  - WAL mode: readers don't block writers, writers don't block readers
  - busy_timeout: wait 5000ms instead of failing immediately on lock
  - synchronous=NORMAL: safe in WAL mode, 2x write performance
  - cache=shared: shared cache across connections
"""

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

is_sqlite = "sqlite" in settings.DATABASE_URL

connect_args: dict = {}
if is_sqlite:
    connect_args = {
        "check_same_thread": False,
        "timeout": 30,  # SQLite busy timeout (seconds)
    }

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args=connect_args,
    pool_size=20 if is_sqlite else 10,
    max_overflow=30 if is_sqlite else 20,
    pool_pre_ping=True,
)


if is_sqlite:
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """Enable WAL mode and performance pragmas for every connection."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.execute("PRAGMA synchronous = NORMAL")
        cursor.execute("PRAGMA busy_timeout = 5000")
        cursor.execute("PRAGMA cache_size = -8000")  # 8MB cache
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA temp_store = MEMORY")
        cursor.close()


async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """FastAPI dependency: yields an async database session.

    Under high concurrency, SQLite may return "database is locked" even with
    WAL mode + busy_timeout. We retry commit up to 3 times with backoff.
    """
    import asyncio

    async with async_session_factory() as session:
        try:
            yield session
            for attempt in range(3):
                try:
                    await session.commit()
                    break
                except Exception as e:
                    if "database is locked" in str(e).lower() and attempt < 2:
                        await asyncio.sleep(0.1 * (attempt + 1))
                        continue
                    raise
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables. Called at application startup."""
    # Import all models to register them with Base.metadata
    import app.models.user  # noqa: F401
    import app.models.session  # noqa: F401
    import app.models.message  # noqa: F401
    import app.models.document  # noqa: F401
    import app.models.audit  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

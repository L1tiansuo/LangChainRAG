"""Database initialization script: creates tables and seeds admin user."""

import asyncio

from sqlalchemy import select

from app.config import settings
from app.core.database import async_session_factory, engine, Base
from app.core.security import hash_password
from app.models.user import User


async def init() -> None:
    """Create tables and seed admin user."""
    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")

    async with async_session_factory() as db:
        # Check if admin exists
        result = await db.execute(select(User).where(User.username == "admin"))
        admin = result.scalar_one_or_none()

        if admin:
            print(f"Admin user already exists (id={admin.id}).")
        else:
            admin = User(
                username="admin",
                password_hash=hash_password("123456"),
                email="admin@example.com",
                role="admin",
            )
            db.add(admin)
            await db.commit()
            await db.refresh(admin)
            print(f"Admin user created: admin / 123456 (id={admin.id})")

    # Ensure data directories
    for dir_path in ["data", settings.UPLOAD_DIR, settings.CHROMA_PERSIST_DIR]:
        path = settings.resolve_path(dir_path)
        path.mkdir(parents=True, exist_ok=True)

    print("Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(init())

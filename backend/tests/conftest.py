"""Shared test fixtures for RAG backend tests.

Uses monkeypatching to override settings for in-memory test database.
"""

import asyncio
import os
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# ── Ensure test database is in-memory ──
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

# Force reimport of config with test settings
# Remove cached modules that read config
for key in list(sys.modules.keys()):
    if key.startswith("app."):
        del sys.modules[key]

# Now import with test settings
from app.config import settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.core.database import (  # noqa: E402
    Base,
    async_session_factory,
    engine,
)

TEST_DIR = Path(__file__).resolve().parent


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create fresh tables before each test (in-memory SQLite)."""
    # Ensure all models are imported and registered
    import app.models.user  # noqa: F401
    import app.models.session  # noqa: F401
    import app.models.message  # noqa: F401
    import app.models.document  # noqa: F401
    import app.models.audit  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    """Async HTTP client connected directly to the FastAPI app."""
    # Import app after settings are configured
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_user():
    """Create an admin user."""
    async with async_session_factory() as db:
        from app.models.user import User
        user = User(
            username="admin",
            password_hash=hash_password("123456"),
            role="admin",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return {"id": user.id, "username": "admin", "password": "123456"}


@pytest_asyncio.fixture
async def normal_user():
    """Create a normal user."""
    async with async_session_factory() as db:
        from app.models.user import User
        user = User(
            username="testuser",
            password_hash=hash_password("test123456"),
            role="user",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return {"id": user.id, "username": "testuser", "password": "test123456"}


@pytest_asyncio.fixture
async def admin_token(client, admin_user):
    """Login as admin and return the auth token."""
    resp = await client.post("/api/v1/auth/login", json={
        "username": "admin", "password": "123456",
    })
    assert resp.status_code == 200, f"Admin login failed: {resp.json()}"
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def user_token(client, normal_user):
    """Login as normal user and return the auth token."""
    resp = await client.post("/api/v1/auth/login", json={
        "username": "testuser", "password": "test123456",
    })
    assert resp.status_code == 200, f"User login failed: {resp.json()}"
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def test_session(client, admin_token):
    """Create a test session and return its ID."""
    resp = await client.post(
        "/api/v1/sessions",
        json={"title": "测试会话"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201, f"Session creation failed: {resp.json()}"
    return resp.json()["id"]

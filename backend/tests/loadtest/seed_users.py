"""Seed script: register 100 test users for load testing.

Usage:
    cd backend
    python tests/loadtest/seed_users.py

Output:
    tests/loadtest/loadtest_users.json — list of {username, password, token}
"""

import asyncio
import json
import sys
from pathlib import Path

import httpx

BASE_URL = "http://localhost:8000/api/v1"
USER_COUNT = 100
PASSWORD = "test123456"
OUTPUT_FILE = Path(__file__).resolve().parent / "loadtest_users.json"


async def register_user(client: httpx.AsyncClient, index: int) -> dict:
    """Register a single user and login to get token."""
    username = f"loadtest_{index:03d}"

    # Try to register (may fail if user already exists — we ignore)
    try:
        await client.post(f"{BASE_URL}/auth/register", json={
            "username": username,
            "password": PASSWORD,
        })
    except Exception:
        pass

    # Login
    resp = await client.post(f"{BASE_URL}/auth/login", json={
        "username": username,
        "password": PASSWORD,
    })

    if resp.status_code != 200:
        raise RuntimeError(f"Login failed for {username}: {resp.status_code}")

    data = resp.json()
    return {
        "username": username,
        "password": PASSWORD,
        "token": data["access_token"],
    }


async def main():
    print(f"Seeding {USER_COUNT} test users...")

    async with httpx.AsyncClient(timeout=10.0) as client:
        users = []
        for i in range(USER_COUNT):
            try:
                user = await register_user(client, i)
                users.append(user)
                if (i + 1) % 20 == 0:
                    print(f"  {i + 1}/{USER_COUNT} done")
            except Exception as e:
                print(f"  Error at user {i}: {e}")

    OUTPUT_FILE.write_text(json.dumps(users, indent=2, ensure_ascii=False))
    print(f"\nDone! {len(users)} users saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())

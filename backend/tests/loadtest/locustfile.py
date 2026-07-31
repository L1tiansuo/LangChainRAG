"""
Locust stress test for RAG Knowledge Base Q&A system.

Simulates 100 concurrent users performing:
  - 70% chance: send a chat query (SSE streaming RAG)
  - 20% chance: list sessions
  - 10% chance: view session messages

Usage:
    cd backend/tests/loadtest
    locust -f locustfile.py --host=http://localhost:8000
    # Open http://localhost:8089 → set users=100, spawn_rate=10
"""

import json
import random
import time
from pathlib import Path

import httpx
from locust import HttpUser, between, events, task

LOADTEST_DIR = Path(__file__).resolve().parent

# ── Load seed data ──
USERS_FILE = LOADTEST_DIR / "loadtest_users.json"
QUESTIONS_FILE = LOADTEST_DIR / "questions.json"

_questions: list[str] = []


def load_questions() -> list[str]:
    global _questions
    if not _questions:
        with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
            _questions = json.load(f)
    return _questions


@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Called once when Locust starts."""
    print(f"\n  Questions loaded: {len(load_questions())}")
    if USERS_FILE.exists():
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
        print(f"  Test users available: {len(users)}\n")
    else:
        print("  ⚠ No pre-seeded users found. Run seed_users.py first.\n")


class RAGUser(HttpUser):
    """Simulates a real user interacting with the RAG system."""

    wait_time = between(3, 8)  # Realistic user think time

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token: str = ""
        self.session_id: str = ""
        self.username: str = ""
        self._user_index: int = -1

    def on_start(self):
        """Login (or register) before starting tasks."""
        # Pick a user from seed pool, or register fresh
        self._user_index = random.randint(0, 99)
        self.username = f"loadtest_{self._user_index:03d}"

        # Try login (user should exist from seed_users.py)
        resp = self.client.post(
            "/api/v1/auth/login",
            json={"username": self.username, "password": "test123456"},
            name="auth: login",
        )

        if resp.status_code == 200:
            self.token = resp.json()["access_token"]
        else:
            # Register + retry login
            self.client.post(
                "/api/v1/auth/register",
                json={"username": self.username, "password": "test123456"},
                name="auth: register",
            )
            resp = self.client.post(
                "/api/v1/auth/login",
                json={"username": self.username, "password": "test123456"},
                name="auth: login",
            )
            if resp.status_code == 200:
                self.token = resp.json()["access_token"]
            else:
                return

        # Create a session for this user
        resp = self.client.post(
            "/api/v1/sessions",
            json={"title": f"压测会话"},
            headers={"Authorization": f"Bearer {self.token}"},
            name="session: create",
        )
        if resp.status_code == 201:
            self.session_id = resp.json()["id"]

    @task(7)
    def ask_question(self):
        """Send a RAG chat query via SSE streaming."""
        if not self.token or not self.session_id:
            return

        question = random.choice(load_questions())

        # Use httpx directly for SSE streaming (Locust client doesn't support streaming well)
        start_time = time.time()
        ttft_recorded = False
        ttft = 0.0
        answer_tokens = 0
        http_status = 0

        try:
            with httpx.stream(
                "POST",
                f"{self.client.base_url}/api/v1/chat/query",
                json={"session_id": self.session_id, "message": question},
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                },
                timeout=60.0,
            ) as response:
                http_status = response.status_code

                if http_status == 200:
                    for line in response.iter_lines():
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                if isinstance(data, dict) and "token" in data:
                                    if not ttft_recorded:
                                        ttft = time.time() - start_time
                                        ttft_recorded = True
                                    answer_tokens += 1
                                elif isinstance(data, dict) and "done" in line:
                                    break  # Done event received
                            except json.JSONDecodeError:
                                pass

            total_time = time.time() - start_time

            if http_status == 200:
                events.request.fire(
                    request_type="SSE",
                    name="chat: RAG query",
                    response_time=total_time * 1000,
                    response_length=answer_tokens,
                )
                # Fire TTFT as a custom event
                if ttft > 0:
                    events.request.fire(
                        request_type="TTFT",
                        name="chat: first token",
                        response_time=ttft * 1000,
                        response_length=1,
                    )
            else:
                events.request.fire(
                    request_type="SSE",
                    name="chat: RAG query",
                    response_time=total_time * 1000,
                    response_length=0,
                    exception=Exception(f"HTTP {http_status}"),
                )

        except Exception as e:
            total_time = time.time() - start_time
            events.request.fire(
                request_type="SSE",
                name="chat: RAG query",
                response_time=total_time * 1000,
                response_length=0,
                exception=e,
            )

    @task(2)
    def list_sessions(self):
        """List the user's conversation sessions."""
        if not self.token:
            return

        self.client.get(
            "/api/v1/sessions",
            headers={"Authorization": f"Bearer {self.token}"},
            name="session: list",
        )

    @task(1)
    def view_messages(self):
        """View messages in the current session."""
        if not self.token or not self.session_id:
            return

        self.client.get(
            f"/api/v1/sessions/{self.session_id}/messages",
            headers={"Authorization": f"Bearer {self.token}"},
            name="session: messages",
        )

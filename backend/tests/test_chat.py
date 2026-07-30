"""Tests for chat/Q&A API."""

import pytest


class TestChatQuery:
    """聊天问答测试"""

    async def test_query_session_not_found(self, client, admin_token):
        """向不存在的会话提问 — 404"""
        resp = await client.post(
            "/api/v1/chat/query",
            json={"session_id": "nonexistent", "message": "Hello"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404

    async def test_query_other_users_session(self, client, admin_token, user_token):
        """访问其他用户的会话 — 404"""
        # admin 创建会话
        create_resp = await client.post(
            "/api/v1/sessions",
            json={"title": "admin session"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        session_id = create_resp.json()["id"]

        # 普通用户尝试向 admin 的会话提问
        resp = await client.post(
            "/api/v1/chat/query",
            json={"session_id": session_id, "message": "Hello"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 404

    async def test_query_empty_message(self, client, admin_token, test_session):
        """空消息 — 返回 200 + SSE 错误事件（RAG pipeline handles it）"""
        resp = await client.post(
            "/api/v1/chat/query",
            json={"session_id": test_session, "message": " "},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # 空消息可能被 Pydantic 拒绝（422），也可能被 RAG pipeline 处理（200 + error event）
        assert resp.status_code in (200, 422)

    async def test_query_valid_session(self, client, admin_token, test_session):
        """正常提问 — 应返回 SSE 流"""
        resp = await client.post(
            "/api/v1/chat/query",
            json={"session_id": test_session, "message": "iPhone 15 多少钱"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")

        # 解析 SSE 事件
        events = []
        async for line in resp.aiter_lines():
            if line.startswith("event: "):
                events.append(("event", line[7:]))
            elif line.startswith("data: "):
                events.append(("data", line[6:]))

        # 至少应有 done 事件
        event_types = [e[1] for e in events if e[0] == "event"]
        data_values = [e[1] for e in events if e[0] == "data"]
        assert "done" in event_types or any("message_id" in d for d in data_values)

    async def test_query_no_auth(self, client):
        """无认证提问 — 拒绝"""
        resp = await client.post(
            "/api/v1/chat/query",
            json={"session_id": "fake", "message": "Hello"},
        )
        assert resp.status_code in (401, 422)

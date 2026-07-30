"""Tests for session management API."""

import pytest


class TestCreateSession:
    """创建会话测试"""

    async def test_create_session_default_title(self, client, admin_token):
        """创建会话（默认标题）"""
        resp = await client.post(
            "/api/v1/sessions",
            json={"title": "新会话"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "新会话"
        assert data["status"] == "active"
        assert "id" in data

    async def test_create_session_custom_title(self, client, admin_token):
        """创建会话（自定义标题）"""
        resp = await client.post(
            "/api/v1/sessions",
            json={"title": "iPhone 咨询"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["title"] == "iPhone 咨询"

    async def test_create_session_no_auth(self, client):
        """无认证创建 — 应拒绝"""
        resp = await client.post("/api/v1/sessions", json={"title": "test"})
        assert resp.status_code in (401, 422)


class TestListSessions:
    """会话列表测试"""

    async def test_list_empty(self, client, admin_token):
        """空列表"""
        resp = await client.get(
            "/api/v1/sessions",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["sessions"] == []

    async def test_list_with_sessions(self, client, admin_token):
        """创建后列表有内容"""
        # Create 3 sessions
        for title in ["会话1", "会话2", "会话3"]:
            await client.post(
                "/api/v1/sessions",
                json={"title": title},
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        resp = await client.get(
            "/api/v1/sessions",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3

    async def test_list_pagination(self, client, admin_token):
        """分页"""
        for i in range(5):
            await client.post(
                "/api/v1/sessions",
                json={"title": f"会话{i}"},
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        resp = await client.get(
            "/api/v1/sessions?page=1&page_size=2",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["sessions"]) == 2
        assert data["total"] == 5

    async def test_user_isolation(self, client, admin_token, user_token):
        """不同用户的会话隔离"""
        await client.post(
            "/api/v1/sessions",
            json={"title": "admin 会话"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        resp = await client.get(
            "/api/v1/sessions",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.json()["total"] == 0  # 普通用户看不到 admin 的会话


class TestSessionDetail:
    """会话详情测试"""

    async def test_get_session(self, client, admin_token, test_session):
        """获取存在的会话"""
        resp = await client.get(
            f"/api/v1/sessions/{test_session}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == test_session

    async def test_get_nonexistent_session(self, client, admin_token):
        """不存在的会话 — 404"""
        resp = await client.get(
            "/api/v1/sessions/nonexistent-id",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404


class TestUpdateSession:
    """更新会话测试"""

    async def test_update_title(self, client, admin_token, test_session):
        """修改标题"""
        resp = await client.patch(
            f"/api/v1/sessions/{test_session}",
            json={"title": "新标题"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "新标题"

    async def test_archive_session(self, client, admin_token, test_session):
        """归档会话"""
        resp = await client.patch(
            f"/api/v1/sessions/{test_session}",
            json={"status": "archived"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "archived"


class TestDeleteSession:
    """删除会话测试"""

    async def test_delete_session(self, client, admin_token, test_session):
        """软删除会话"""
        resp = await client.delete(
            f"/api/v1/sessions/{test_session}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200

        # 删除后列表不再显示
        resp2 = await client.get(
            "/api/v1/sessions",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp2.json()["total"] == 0

"""Tests for authentication API."""

import pytest


class TestRegister:
    """用户注册测试"""

    async def test_register_success(self, client):
        """正常注册 — 应返回 201"""
        resp = await client.post("/api/v1/auth/register", json={
            "username": "newuser", "password": "password123",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "newuser"
        assert "user_id" in data

    async def test_register_duplicate_username(self, client):
        """重复用户名 — 应返回 409"""
        await client.post("/api/v1/auth/register", json={
            "username": "dupuser", "password": "password123",
        })
        resp = await client.post("/api/v1/auth/register", json={
            "username": "dupuser", "password": "password456",
        })
        assert resp.status_code == 409

    async def test_register_short_username(self, client):
        """用户名过短 — 应返回 422"""
        resp = await client.post("/api/v1/auth/register", json={
            "username": "ab", "password": "password123",
        })
        assert resp.status_code == 422

    async def test_register_short_password(self, client):
        """密码过短 — 应返回 422"""
        resp = await client.post("/api/v1/auth/register", json={
            "username": "validuser", "password": "123",
        })
        assert resp.status_code == 422

    async def test_register_with_email(self, client):
        """带邮箱注册 — 应返回 201"""
        resp = await client.post("/api/v1/auth/register", json={
            "username": "emailuser", "password": "password123",
            "email": "user@example.com",
        })
        assert resp.status_code == 201


class TestLogin:
    """用户登录测试"""

    async def test_login_as_admin(self, client, admin_user):
        """admin 登录 — 应返回 200 + token"""
        resp = await client.post("/api/v1/auth/login", json={
            "username": "admin", "password": "123456",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "admin"
        assert data["user"]["role"] == "admin"

    async def test_login_wrong_password(self, client, admin_user):
        """错误密码 — 应返回 401"""
        resp = await client.post("/api/v1/auth/login", json={
            "username": "admin", "password": "wrongpassword",
        })
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client):
        """不存在的用户 — 应返回 401"""
        resp = await client.post("/api/v1/auth/login", json={
            "username": "ghost", "password": "123456",
        })
        assert resp.status_code == 401

    async def test_login_empty_body(self, client):
        """空请求体 — 应返回 422"""
        resp = await client.post("/api/v1/auth/login", json={})
        assert resp.status_code == 422


class TestGetMe:
    """获取当前用户信息测试"""

    async def test_get_me_with_token(self, client, admin_token):
        """有效 token — 应返回用户信息"""
        resp = await client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {admin_token}",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "admin"
        assert data["role"] == "admin"

    async def test_get_me_without_token(self, client):
        """无 token — 应返回 401（FastAPI 自动拒绝缺少 Header 的请求为 422）"""
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code in (401, 422)

    async def test_get_me_invalid_token(self, client):
        """无效 token — 应返回 401"""
        resp = await client.get("/api/v1/auth/me", headers={
            "Authorization": "Bearer invalid_token_here",
        })
        assert resp.status_code == 401


class TestChangePassword:
    """修改密码测试"""

    async def test_change_password_success(self, client, admin_token):
        """正确修改密码 — 应返回 200，新密码可登录"""
        resp = await client.post(
            "/api/v1/auth/change-password",
            json={"old_password": "123456", "new_password": "newpass123"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200

        # 验证新密码可登录
        resp2 = await client.post("/api/v1/auth/login", json={
            "username": "admin", "password": "newpass123",
        })
        assert resp2.status_code == 200

    async def test_change_password_wrong_old(self, client, admin_token):
        """旧密码错误 — 应返回 400"""
        resp = await client.post(
            "/api/v1/auth/change-password",
            json={"old_password": "wrongpassword", "new_password": "newpass123"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 400

    async def test_change_password_too_short(self, client, admin_token):
        """新密码太短 — 应返回 422"""
        resp = await client.post(
            "/api/v1/auth/change-password",
            json={"old_password": "123456", "new_password": "123"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422


class TestLogout:
    """退出登录测试"""

    async def test_logout_success(self, client, admin_token):
        """正常退出 — 应返回 200"""
        resp = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert "退出" in resp.json()["message"] or "out" in resp.json()["message"].lower()

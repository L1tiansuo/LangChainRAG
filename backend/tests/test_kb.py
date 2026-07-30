"""Tests for knowledge base management API."""

import io
import pytest


class TestKBStats:
    """知识库统计测试"""

    async def test_get_stats_as_admin(self, client, admin_token):
        """管理员获取统计"""
        resp = await client.get(
            "/api/v1/kb/stats",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_documents" in data
        assert "total_chunks" in data

    async def test_get_stats_as_user_denied(self, client, user_token):
        """普通用户无权限"""
        resp = await client.get(
            "/api/v1/kb/stats",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403

    async def test_get_stats_no_auth(self, client):
        """无认证"""
        resp = await client.get("/api/v1/kb/stats")
        assert resp.status_code in (401, 422)


class TestDocumentsList:
    """文档列表测试"""

    async def test_list_empty(self, client, admin_token):
        """空文档列表"""
        resp = await client.get(
            "/api/v1/kb/documents",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["documents"] == []

    async def test_list_as_user_denied(self, client, user_token):
        """普通用户无权限"""
        resp = await client.get(
            "/api/v1/kb/documents",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403


class TestDocumentUpload:
    """文档上传测试"""

    async def test_upload_csv(self, client, admin_token):
        """上传 CSV 文件"""
        csv_content = "name,price,category\niPhone 15,5999,phone\n".encode("utf-8")
        files = {"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
        resp = await client.post(
            "/api/v1/kb/documents/upload",
            files=files,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 202
        assert "document_id" in resp.json()

    async def test_upload_unsupported_type(self, client, admin_token):
        """上传不支持的文件类型"""
        files = {"file": ("test.exe", io.BytesIO(b"fake"), "application/octet-stream")}
        resp = await client.post(
            "/api/v1/kb/documents/upload",
            files=files,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 400

    async def test_upload_as_user_denied(self, client, user_token):
        """普通用户无权限上传"""
        files = {"file": ("test.csv", io.BytesIO(b"data"), "text/csv")}
        resp = await client.post(
            "/api/v1/kb/documents/upload",
            files=files,
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403


class TestDocumentDetail:
    """文档详情测试"""

    async def test_get_nonexistent_document(self, client, admin_token):
        """不存在的文档 — 404"""
        resp = await client.get(
            "/api/v1/kb/documents/nonexistent",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404


class TestChunks:
    """分块列表测试"""

    async def test_list_chunks_no_document(self, client, admin_token):
        """缺少 document_id 参数 — 422"""
        resp = await client.get(
            "/api/v1/kb/chunks",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422

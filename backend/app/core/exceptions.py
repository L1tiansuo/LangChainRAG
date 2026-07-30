"""Custom exceptions and FastAPI exception handlers."""

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class AppError:
    """Standardized error codes."""

    # Auth
    INVALID_CREDENTIALS = ("INVALID_CREDENTIALS", "用户名或密码错误")
    USERNAME_EXISTS = ("USERNAME_EXISTS", "用户名已存在")
    TOKEN_EXPIRED = ("TOKEN_EXPIRED", "登录已过期，请重新登录")
    INVALID_TOKEN = ("INVALID_TOKEN", "无效的认证令牌")
    OLD_PASSWORD_WRONG = ("OLD_PASSWORD_WRONG", "当前密码错误")

    # Permission
    FORBIDDEN = ("FORBIDDEN", "无权限执行此操作")
    ADMIN_ONLY = ("ADMIN_ONLY", "仅管理员可执行此操作")

    # Resource
    NOT_FOUND = ("NOT_FOUND", "资源不存在")
    SESSION_NOT_FOUND = ("SESSION_NOT_FOUND", "会话不存在")
    DOCUMENT_NOT_FOUND = ("DOCUMENT_NOT_FOUND", "文档不存在")

    # Document
    FILE_TOO_LARGE = ("FILE_TOO_LARGE", "文件大小超过限制（最大 20MB）")
    UNSUPPORTED_TYPE = ("UNSUPPORTED_TYPE", "不支持的文件类型")
    PROCESSING_FAILED = ("PROCESSING_FAILED", "文档处理失败")

    # Rate Limit
    RATE_LIMITED = ("RATE_LIMITED", "请求过于频繁，请稍后再试")

    # RAG
    RETRIEVAL_FAILED = ("RETRIEVAL_FAILED", "知识库检索失败")
    LLM_FAILED = ("LLM_FAILED", "AI 服务调用失败")


def raise_app_error(error_tuple: tuple[str, str], status_code: int = 400) -> None:
    """Raise an HTTPException with standardized error format."""
    code, message = error_tuple
    raise HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message},
    )


async def app_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Global exception handler for consistent error responses."""
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "UNKNOWN", "message": str(exc.detail)}},
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all exception handler."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": "INTERNAL_ERROR", "message": "服务器内部错误"}},
    )

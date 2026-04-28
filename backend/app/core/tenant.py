"""
多租户中间件
自动注入 tenant_id 到请求状态，请求结束后自动清理上下文
"""
from contextvars import ContextVar
from typing import Optional

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_access_token


# Bearer Token 认证
bearer_scheme = HTTPBearer(auto_error=False)

# ContextVar for thread/coroutine-safe tenant context
_tenant_id_var: ContextVar[Optional[str]] = ContextVar('tenant_id', default=None)
_user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


class TenantContext:
    """租户上下文（基于 ContextVar，线程/协程安全）"""

    @classmethod
    def set(cls, tenant_id: str, user_id: str) -> None:
        _tenant_id_var.set(tenant_id)
        _user_id_var.set(user_id)

    @classmethod
    def get_tenant_id(cls) -> Optional[str]:
        return _tenant_id_var.get()

    @classmethod
    def get_user_id(cls) -> Optional[str]:
        return _user_id_var.get()

    @classmethod
    def clear(cls) -> None:
        _tenant_id_var.set(None)
        _user_id_var.set(None)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    获取当前认证用户
    依赖注入到路由
    
    Returns:
        包含 user_id, tenant_id 的用户信息字典
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = verify_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: str = payload.get("sub")
    tenant_id: str = payload.get("tenant_id")
    
    if not user_id or not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 数据不完整",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 设置租户上下文
    TenantContext.set(tenant_id, user_id)
    
    # 将用户信息附加到请求状态
    request.state.user_id = user_id
    request.state.tenant_id = tenant_id
    
    return {
        "user_id": user_id,
        "tenant_id": tenant_id,
    }


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[dict]:
    """
    可选的认证获取（不强制认证）
    用于公开接口的匿名访问
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = verify_access_token(token)
    
    if payload:
        return {
            "user_id": payload.get("sub"),
            "tenant_id": payload.get("tenant_id"),
        }
    return None


def get_tenant_id() -> str:
    """获取当前租户ID（从上下文）"""
    tenant_id = TenantContext.get_tenant_id()
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="缺少租户上下文",
        )
    return tenant_id


class TenantContextCleanupMiddleware(BaseHTTPMiddleware):
    """
    请求结束后自动清理 TenantContext

    防止 ContextVar 中的 tenant_id/user_id 在请求结束后仍然残留，
    虽然在标准 asyncio 中每个请求是独立协程，但在某些 ASGI 服务器
    (如 uvicorn + asyncio) 中协程可能被复用，导致上下文泄漏。
    """

    async def dispatch(self, request: Request, call_next):
        try:
            response: Response = await call_next(request)
            return response
        finally:
            # 请求结束后（无论成功还是异常）清理租户上下文
            TenantContext.clear()

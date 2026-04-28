"""
多租户中间件
自动注入 tenant_id 到请求状态
"""
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_access_token


# Bearer Token 认证
bearer_scheme = HTTPBearer(auto_error=False)


class TenantContext:
    """租户上下文（线程安全）"""
    
    _tenant_id: Optional[str] = None
    _user_id: Optional[str] = None
    
    @classmethod
    def set(cls, tenant_id: str, user_id: str) -> None:
        cls._tenant_id = tenant_id
        cls._user_id = user_id
    
    @classmethod
    def get_tenant_id(cls) -> Optional[str]:
        return cls._tenant_id
    
    @classmethod
    def get_user_id(cls) -> Optional[str]:
        return cls._user_id
    
    @classmethod
    def clear(cls) -> None:
        cls._tenant_id = None
        cls._user_id = None


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

"""
认证 API 路由
实现用户注册、登录、登出、Token 刷新等功能
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis_client import add_token_to_blacklist, is_token_blacklisted
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_access_token,
    verify_password,
    verify_refresh_token,
)
from app.core.tenant import get_current_user
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RegisterRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["认证"])

# Bearer Token 认证方案
bearer_scheme = HTTPBearer(auto_error=False)


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    用户注册 - 同时创建租户
    
    流程：
    1. 检查邮箱是否已存在
    2. 创建租户（org_name 作为租户名称）
    3. 创建用户（关联到租户）
    4. 签发 JWT Token
    """
    # 检查邮箱是否已存在
    existing = await db.execute(
        select(User).where(User.email == req.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="邮箱已被注册"
        )
    
    # 创建租户
    tenant_name = req.org_name or req.email.split("@")[0]
    tenant = Tenant(name=tenant_name)
    db.add(tenant)
    await db.flush()  # 获取 tenant.id
    
    # 创建用户
    user = User(
        tenant_id=tenant.id,
        email=req.email,
        password_hash=get_password_hash(req.password),
        name=req.name or req.email.split("@")[0],
        role="admin",  # 第一个用户是管理员
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 签发 Token
    access_token = create_access_token(
        data={"sub": user.id, "tenant_id": tenant.id}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.id, "tenant_id": tenant.id}
    )
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    req: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    用户登录
    
    验证邮箱和密码，成功后签发 JWT Token
    """
    result = await db.execute(
        select(User).where(User.email == req.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误"
        )
    
    # 更新最后登录时间
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    
    access_token = create_access_token(
        data={"sub": user.id, "tenant_id": user.tenant_id}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.id, "tenant_id": user.tenant_id}
    )
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
):
    """
    用户登出 - Token 加入黑名单
    
    将当前 Access Token 加入 Redis 黑名单，使其立即失效
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供 Token"
        )
    
    token = credentials.credentials
    payload = verify_access_token(token)
    
    if payload:
        # 计算 Token 剩余有效期
        exp = payload.get("exp", 0)
        ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 0)
        
        # 加入黑名单（使用 jti 或 token 哈希）
        jti = payload.get("jti") or token[-32:]  # 如果没有 jti，使用 token 后 32 位
        if ttl > 0:
            await add_token_to_blacklist(jti, ttl)
    
    return LogoutResponse(message="登出成功")


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    req: RefreshTokenRequest,
):
    """
    刷新 Access Token
    
    使用 Refresh Token 换取新的 Access Token
    """
    payload = verify_refresh_token(req.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token 无效或已过期"
        )
    
    # 验证 refresh_token 未被加入黑名单
    jti = payload.get("jti") or req.refresh_token[-32:]
    if await is_token_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token 已失效"
        )
    
    # 签发新的 Access Token
    new_access_token = create_access_token(
        data={"sub": payload["sub"], "tenant_id": payload["tenant_id"]}
    )
    
    return RefreshTokenResponse(
        access_token=new_access_token,
        refresh_token=req.refresh_token,  # 保持原 refresh_token
        token_type="bearer",
    )


@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户信息
    
    需要 Bearer Token 认证
    """
    result = await db.execute(
        select(User).where(User.id == current_user["user_id"])
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return UserResponse.model_validate(user)

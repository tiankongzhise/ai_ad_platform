"""
广告账户 API 路由
包含巨量引擎/百度营销 OAuth 授权和广告数据管理
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import (
    AdPlatformError,
    AuthenticationError,
    ResourceNotFoundError,
    ValidationError,
)
from app.core.tenant import get_current_user, TenantContext
from app.models.ad_account import AdAccount, AdAccountStatus, AdPlatform
from app.schemas.ad_account import (
    AdAccountListResponse,
    AdAccountResponse,
    AdAccountUpdate,
    ManualSyncRequest,
    ManualSyncResponse,
    OAuthCallbackResponse,
    SyncStatusResponse,
)
from app.services.juliang_service import JuliangService, get_juliang_service


router = APIRouter(prefix="/ad", tags=["广告账户"])


# ==================== OAuth 授权相关 ====================

@router.get("/juliang/oauth-url")
async def get_juliang_oauth_url(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    获取巨量引擎 OAuth 授权 URL
    
    返回授权跳转地址，前端需要跳转到此地址进行授权
    """
    # 生成随机 state 防止 CSRF
    state = secrets.token_urlsafe(32)
    
    # 将 state 存入 Redis（临时存储，后续回调验证）
    # TODO: 存入 Redis，设置 10 分钟过期
    # await redis.setex(f"oauth_state:{state}", 600, current_user["tenant_id"])
    
    service = get_juliang_service()
    oauth_url = service.build_oauth_url(state)
    
    return {
        "oauth_url": oauth_url,
        "state": state,
    }


@router.get("/juliang/callback", response_model=OAuthCallbackResponse)
async def juliang_oauth_callback(
    code: str = Query(..., description="授权码"),
    state: Optional[str] = Query(None, description="状态参数"),
    db: AsyncSession = Depends(get_db),
):
    """
    巨量引擎 OAuth 回调处理
    
    流程:
    1. 通过授权码换取 Access Token
    2. 获取广告账户信息
    3. 存储 Token 和账户信息
    4. 立即触发 7 天历史数据拉取（关键改进）
    """
    try:
        service = get_juliang_service()
        
        # 1. 换取 Token
        token_info = await service.exchange_token(code)
        
        # 2. 获取广告账户信息
        # 注意：巨量引擎授权后需要先获取广告主列表
        service.set_tokens(token_info.access_token, token_info.refresh_token)
        
        # 3. 获取账户详情（如果授权了多个账户，使用第一个）
        if token_info.advertiser_ids:
            advertiser_id = token_info.advertiser_ids[0]
            advertisers = await service.get_advertiser_list(
                access_token=token_info.access_token
            )
            
            # 找到对应的账户信息
            advertiser = next(
                (a for a in advertisers if a.advertiser_id == advertiser_id),
                None
            )
            
            if not advertiser:
                advertiser = advertisers[0]
            
            account_name = advertiser.advertiser_name
            balance = advertiser.balance
        else:
            # 如果没有返回账户ID，使用默认值
            advertiser_id = f"jl_{secrets.token_hex(8)}"
            account_name = "巨量引擎广告账户"
            balance = 0.0
        
        # 4. 获取当前租户ID（从 state 或默认）
        # 实际生产中应该从 Redis 中恢复 state 对应的 tenant_id
        tenant_id = "default_tenant"  # TODO: 从 Redis/数据库恢复
        
        # 5. 存储广告账户信息
        ad_account = AdAccount(
            tenant_id=tenant_id,
            platform=AdPlatform.JULIANG,
            account_id=str(advertiser_id),
            account_name=account_name,
            access_token=token_info.access_token,
            refresh_token=token_info.refresh_token,
            token_expires_at=datetime.now() + timedelta(seconds=token_info.expires_in),
            balance=balance,
            status=AdAccountStatus.ACTIVE,
        )
        
        db.add(ad_account)
        await db.commit()
        await db.refresh(ad_account)
        
        # 6. 立即触发 Celery 任务拉取 7 天历史数据（关键改进）
        # 这是解决 UX BP-3 "绑定后无数据" 的核心
        try:
            from app.tasks.sync_ad_tasks import sync_ad_data_juliang
            sync_ad_data_juliang.delay(ad_account.id, days=7)
        except Exception as e:
            # 即使 Celery 失败，也返回成功，因为 OAuth 已经完成
            import structlog
            logger = structlog.get_logger()
            logger.warning("立即同步任务触发失败", account_id=ad_account.id, error=str(e))
        
        return OAuthCallbackResponse(
            status="success",
            ad_account_id=ad_account.id,
            account_name=account_name,
            next_step="crm_import",
            message="巨量引擎授权成功，正在后台同步广告数据",
        )
        
    except AdPlatformError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"巨量引擎授权失败: {e.detail}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"授权处理异常: {str(e)}",
        )


# ==================== 广告账户管理 ====================

@router.get("/accounts", response_model=AdAccountListResponse)
async def list_ad_accounts(
    platform: Optional[str] = Query(None, description="平台筛选: juliang | baidu"),
    status_filter: Optional[str] = Query(None, alias="status", description="状态筛选"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    获取广告账户列表
    """
    query = select(AdAccount).where(AdAccount.tenant_id == current_user["tenant_id"])
    
    if platform:
        query = query.where(AdAccount.platform == platform)
    if status_filter:
        query = query.where(AdAccount.status == status_filter)
    
    query = query.order_by(AdAccount.created_at.desc())
    
    result = await db.execute(query)
    accounts = result.scalars().all()
    
    return AdAccountListResponse(
        items=[AdAccountResponse.model_validate(acc) for acc in accounts],
        total=len(accounts),
    )


@router.get("/accounts/{account_id}", response_model=AdAccountResponse)
async def get_ad_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    获取单个广告账户详情
    """
    query = select(AdAccount).where(
        AdAccount.id == account_id,
        AdAccount.tenant_id == current_user["tenant_id"],
    )
    result = await db.execute(query)
    account = result.scalar_one_or_none()
    
    if not account:
        raise ResourceNotFoundError("广告账户", account_id)
    
    return AdAccountResponse.model_validate(account)


@router.delete("/accounts/{account_id}")
async def delete_ad_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    断开广告账户
    """
    query = select(AdAccount).where(
        AdAccount.id == account_id,
        AdAccount.tenant_id == current_user["tenant_id"],
    )
    result = await db.execute(query)
    account = result.scalar_one_or_none()
    
    if not account:
        raise ResourceNotFoundError("广告账户", account_id)
    
    # 软删除：标记为暂停状态
    account.status = AdAccountStatus.SUSPENDED
    await db.commit()
    
    return {"message": "广告账户已断开"}


@router.post("/accounts/{account_id}/sync", response_model=ManualSyncResponse)
async def manual_sync_ad_data(
    account_id: str,
    body: ManualSyncRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    手动触发广告数据同步
    """
    query = select(AdAccount).where(
        AdAccount.id == account_id,
        AdAccount.tenant_id == current_user["tenant_id"],
    )
    result = await db.execute(query)
    account = result.scalar_one_or_none()
    
    if not account:
        raise ResourceNotFoundError("广告账户", account_id)
    
    if account.platform != AdPlatform.JULIANG:
        raise ValidationError(detail="当前仅支持巨量引擎手动同步")
    
    # 触发 Celery 任务
    from app.tasks.sync_ad_tasks import sync_ad_data_juliang
    
    task = sync_ad_data_juliang.delay(account_id, days=body.days)
    
    return ManualSyncResponse(
        task_id=task.id,
        message=f"已提交同步任务，预计需要 {body.days * 2} 分钟完成",
        estimated_completion=(datetime.now() + timedelta(minutes=body.days * 2)).isoformat(),
    )


# ==================== 同步状态 ====================

@router.get("/sync-status", response_model=SyncStatusResponse)
async def get_sync_status(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    获取广告同步状态（用于仪表盘空态判定）
    
    返回:
    - ad_accounts_bound: 是否已绑定广告账户
    - has_ad_data: 是否有广告数据
    - sync_in_progress: 是否有同步任务进行中
    - last_sync_at: 最后同步时间
    - sync_error: 同步错误信息
    """
    # 检查是否绑定广告账户
    query = select(AdAccount).where(
        AdAccount.tenant_id == current_user["tenant_id"],
        AdAccount.status == AdAccountStatus.ACTIVE,
    )
    result = await db.execute(query)
    accounts = result.scalars().all()
    
    ad_accounts_bound = len(accounts) > 0
    
    # 检查是否有广告数据
    if ad_accounts_bound:
        from app.models.ad_daily_stat import AdDailyStat
        data_query = select(AdDailyStat).where(
            AdDailyStat.tenant_id == current_user["tenant_id"]
        ).limit(1)
        data_result = await db.execute(data_query)
        has_ad_data = data_result.scalar_one_or_none() is not None
    else:
        has_ad_data = False
    
    # TODO: 检查 Redis/Celery 中的同步任务状态
    sync_in_progress = False
    last_sync_at = None
    sync_error = None
    
    return SyncStatusResponse(
        ad_accounts_bound=ad_accounts_bound,
        has_ad_data=has_ad_data,
        sync_in_progress=sync_in_progress,
        last_sync_at=last_sync_at,
        sync_error=sync_error,
    )

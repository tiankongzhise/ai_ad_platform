"""
广告账户 API 路由
包含巨量引擎/百度营销 OAuth 授权和广告数据管理

OAuth 回调链路说明
─────────────────
广告平台（巨量引擎 / 百度）在用户授权后，会将 code 和 state 以 Query String 形式
拼接在我们事先注册的 redirect_uri 上，向我们的后端发起一次 GET 请求：

    GET /api/v1/ad/juliang/callback?code=AUTH_CODE_XXX&state=RANDOM_STATE
    GET /api/v1/ad/baidu/callback?code=AUTH_CODE_XXX&state=RANDOM_STATE

后端从 URL 的 Query String 中解析这两个参数：
  • code  ——  一次性授权码，调用平台 Token 接口换取 access_token
  • state ——  我们在发起授权时生成的随机字符串，用于防 CSRF + 还原 tenant_id

完整流程：
  1. 前端调用 /ad/juliang/oauth-url → 后端生成 state，存 Redis（oauth_state:{state}），
     返回授权 URL 给前端
  2. 前端跳转到授权 URL，用户完成授权
  3. 广告平台重定向到 /api/v1/ad/juliang/callback?code=XXX&state=XXX
  4. 后端从 Redis 取出 state 对应的 tenant_id（消费并删除，防重放）
  5. 用 code 换取 access_token
  6. 存储账户信息到数据库
  7. 立即触发 Celery 任务拉取历史数据
  8. 302 重定向到前端绑定成功页（带 account_id 参数）
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import (
    AdPlatformError,
    ResourceNotFoundError,
    ValidationError,
)
from app.core.redis_client import (
    consume_oauth_state,
    get_sync_status,
    save_oauth_state,
    set_sync_status,
)
from app.core.tenant import get_current_user
from app.models.ad_account import AdAccount, AdAccountStatus, AdPlatform
from app.schemas.ad_account import (
    AdAccountListResponse,
    AdAccountResponse,
    AdAccountUpdate,
    ManualSyncRequest,
    ManualSyncResponse,
    SyncStatusResponse,
)
from app.services.baidu_service import BaiduService, get_baidu_service
from app.services.juliang_service import JuliangService, get_juliang_service

router = APIRouter(prefix="/ad", tags=["广告账户"])
logger = structlog.get_logger()


# ============================================================
# OAuth 授权：发起阶段
# ============================================================

@router.get("/juliang/oauth-url", summary="获取巨量引擎 OAuth 授权 URL")
async def get_juliang_oauth_url(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    获取巨量引擎 OAuth 授权 URL。

    前端收到 oauth_url 后直接跳转（window.location.href = oauth_url）。

    内部逻辑：
      1. 生成随机 state（urlsafe 32字节）
      2. 将 state → {tenant_id, user_id} 存入 Redis，TTL=10分钟
      3. 返回携带 state 的授权 URL
    """
    state = secrets.token_urlsafe(32)

    # 将 state 与当前用户绑定，回调时用于还原 tenant_id
    await save_oauth_state(
        state=state,
        tenant_id=current_user["tenant_id"],
        user_id=current_user["user_id"],
    )

    service = get_juliang_service()
    oauth_url = service.build_oauth_url(state)

    logger.info(
        "生成巨量引擎 OAuth URL",
        tenant_id=current_user["tenant_id"],
        state=state[:8] + "...",   # 日志中只打印前8位
    )

    return {"oauth_url": oauth_url, "state": state}


@router.get("/baidu/oauth-url", summary="获取百度营销 OAuth 授权 URL")
async def get_baidu_oauth_url(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    获取百度营销 OAuth 授权 URL（逻辑同巨量引擎）。
    """
    state = secrets.token_urlsafe(32)

    await save_oauth_state(
        state=state,
        tenant_id=current_user["tenant_id"],
        user_id=current_user["user_id"],
    )

    service = get_baidu_service()
    oauth_url = service.build_oauth_url(state)

    logger.info(
        "生成百度营销 OAuth URL",
        tenant_id=current_user["tenant_id"],
        state=state[:8] + "...",
    )

    return {"oauth_url": oauth_url, "state": state}


# ============================================================
# OAuth 回调：广告平台重定向到此端点
# ============================================================

@router.get("/juliang/callback", summary="巨量引擎 OAuth 回调")
async def juliang_oauth_callback(
    code: str = Query(..., description="巨量引擎回传的一次性授权码"),
    state: Optional[str] = Query(None, description="防 CSRF 状态参数，与发起时一致"),
    error: Optional[str] = Query(None, description="用户拒绝授权时平台传入的错误码"),
    db: AsyncSession = Depends(get_db),
):
    """
    巨量引擎 OAuth 回调处理。

    广告平台在用户完成授权后，将 code 和 state 拼在 redirect_uri 上发起 GET 请求，
    本接口接收并处理：

      1. 检查 error 参数（用户拒绝授权时处理）
      2. 验证 state（从 Redis 消费，防 CSRF + 还原 tenant_id）
      3. 用 code 换取 access_token / refresh_token
      4. 获取广告主列表，创建 AdAccount 记录
      5. 触发 Celery 任务立即拉取 7 天历史数据
      6. 302 重定向到前端绑定成功页

    Query 参数（由广告平台拼入 URL）：
      - code:  授权码（一次性，有效期约5分钟）
      - state: 我们发起时传入的随机串
      - error: 用户取消/拒绝授权时平台传入（此时没有 code）
    """
    # ── 0. 用户拒绝授权 ──────────────────────────────────────────
    if error:
        logger.warning("巨量引擎授权被用户拒绝", error=error)
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/ad-accounts?oauth_result=cancelled&platform=juliang",
            status_code=302,
        )

    # ── 1. 验证 state，还原 tenant_id ─────────────────────────────
    tenant_id: Optional[str] = None
    if state:
        user_ctx = await consume_oauth_state(state)
        if user_ctx:
            tenant_id = user_ctx["tenant_id"]
        else:
            logger.warning(
                "OAuth state 无效或已过期，可能遭受 CSRF 攻击",
                state=state[:8] + "...",
            )
            # state 无效时，拒绝处理，重定向到错误页
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/ad-accounts?oauth_result=error"
                    "&platform=juliang&reason=invalid_state",
                status_code=302,
            )

    # state 为空时：生产环境拒绝，开发环境降级
    if not tenant_id:
        if settings.DEBUG:
            logger.warning("OAuth 回调未携带有效 state，降级到默认租户（仅开发环境）")
            tenant_id = "default_tenant"
        else:
            logger.warning("生产环境拒绝无 state 的 OAuth 回调")
            return RedirectResponse(
                url=(
                    f"{settings.FRONTEND_URL}/ad-accounts"
                    f"?oauth_result=error&platform=juliang&reason=missing_state"
                ),
                status_code=302,
            )

    try:
        service = get_juliang_service()

        # ── 2. 用授权码换取 Token ───────────────────────────────────
        token_info = await service.exchange_token(code)
        service.set_tokens(token_info.access_token, token_info.refresh_token)

        logger.info(
            "巨量引擎 Token 换取成功",
            tenant_id=tenant_id,
            advertiser_count=len(token_info.advertiser_ids),
        )

        # ── 3. 获取广告主信息 ───────────────────────────────────────
        if token_info.advertiser_ids:
            advertiser_id = token_info.advertiser_ids[0]
            advertisers = await service.get_advertiser_list(
                access_token=token_info.access_token
            )
            advertiser = next(
                (a for a in advertisers if a.advertiser_id == advertiser_id),
                advertisers[0] if advertisers else None,
            )
            account_name = advertiser.advertiser_name if advertiser else "巨量引擎广告账户"
            balance = advertiser.balance if advertiser else 0.0
        else:
            advertiser_id = f"jl_{secrets.token_hex(8)}"
            account_name = "巨量引擎广告账户"
            balance = 0.0

        # ── 4. 幂等写入 AdAccount（已存在则更新 Token）──────────────
        existing_query = select(AdAccount).where(
            AdAccount.tenant_id == tenant_id,
            AdAccount.platform == AdPlatform.JULIANG,
            AdAccount.account_id == str(advertiser_id),
        )
        existing_result = await db.execute(existing_query)
        ad_account = existing_result.scalar_one_or_none()

        if ad_account:
            # 已绑定：刷新 Token 和状态
            ad_account.access_token = token_info.access_token
            ad_account.refresh_token = token_info.refresh_token
            ad_account.token_expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=token_info.expires_in
            )
            ad_account.balance = balance
            ad_account.status = AdAccountStatus.ACTIVE
            logger.info("巨量引擎账户 Token 已刷新", account_id=ad_account.id)
        else:
            # 新绑定：创建账户记录
            ad_account = AdAccount(
                tenant_id=tenant_id,
                platform=AdPlatform.JULIANG,
                account_id=str(advertiser_id),
                account_name=account_name,
                access_token=token_info.access_token,
                refresh_token=token_info.refresh_token,
                token_expires_at=datetime.now(timezone.utc) + timedelta(
                    seconds=token_info.expires_in
                ),
                balance=balance,
                status=AdAccountStatus.ACTIVE,
            )
            db.add(ad_account)

        await db.commit()
        await db.refresh(ad_account)

        # ── 5. 立即触发 Celery 任务拉取 7 天历史数据（解决 UX BP-3）──
        try:
            from app.tasks.sync_ad_tasks import sync_ad_data_juliang

            sync_ad_data_juliang.delay(ad_account.id, days=7)

            # 写入同步状态到 Redis，供前端轮询
            await set_sync_status(
                account_id=ad_account.id,
                status_data={
                    "status": "running",
                    "progress": 0,
                    "synced_count": 0,
                    "error_msg": None,
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "finished_at": None,
                },
            )
            logger.info("已触发立即同步任务", account_id=ad_account.id)
        except Exception as celery_err:
            # Celery 触发失败不影响授权成功
            logger.warning(
                "立即同步任务触发失败",
                account_id=ad_account.id,
                error=str(celery_err),
            )

        # ── 6. 重定向到前端成功页 ───────────────────────────────────
        return RedirectResponse(
            url=(
                f"{settings.FRONTEND_URL}/ad-accounts"
                f"?oauth_result=success"
                f"&platform=juliang"
                f"&account_id={ad_account.id}"
                f"&account_name={account_name}"
            ),
            status_code=302,
        )

    except AdPlatformError as e:
        logger.error("巨量引擎 OAuth 处理失败", error=e.detail)
        return RedirectResponse(
            url=(
                f"{settings.FRONTEND_URL}/ad-accounts"
                f"?oauth_result=error&platform=juliang&reason={e.detail}"
            ),
            status_code=302,
        )
    except Exception as e:
        logger.error("巨量引擎 OAuth 未知异常", error=str(e))
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/ad-accounts?oauth_result=error&platform=juliang",
            status_code=302,
        )


@router.get("/baidu/callback", summary="百度营销 OAuth 回调")
async def baidu_oauth_callback(
    code: str = Query(..., description="百度回传的一次性授权码"),
    state: Optional[str] = Query(None, description="防 CSRF 状态参数，与发起时一致"),
    error: Optional[str] = Query(None, description="用户拒绝授权时平台传入的错误码"),
    error_description: Optional[str] = Query(None, description="错误描述"),
    db: AsyncSession = Depends(get_db),
):
    """
    百度营销 OAuth 回调处理。

    Query 参数（由百度拼入 URL）：
      - code:              授权码（一次性）
      - state:             我们发起时传入的随机串
      - error:             授权失败时的错误码（access_denied 等）
      - error_description: 错误描述
    """
    # ── 0. 用户拒绝授权 ──────────────────────────────────────────
    if error:
        logger.warning("百度营销授权被用户拒绝", error=error, desc=error_description)
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/ad-accounts?oauth_result=cancelled&platform=baidu",
            status_code=302,
        )

    # ── 1. 验证 state，还原 tenant_id ─────────────────────────────
    import os
    tenant_id: Optional[str] = None
    if state:
        user_ctx = await consume_oauth_state(state)
        if user_ctx:
            tenant_id = user_ctx["tenant_id"]
        else:
            logger.warning("百度 OAuth state 无效或已过期", state=state[:8] + "...")
            return RedirectResponse(
                url=(
                    f"{settings.FRONTEND_URL}/ad-accounts"
                    f"?oauth_result=error&platform=baidu&reason=invalid_state"
                ),
                status_code=302,
            )

    # 生产环境强制要求 state
    if not tenant_id:
        allow_downgrade = os.getenv("ALLOW_OAUTH_STATE_DOWNGRADE", "false").lower() == "true"
        if not allow_downgrade:
            logger.warning("生产环境拒绝无 state 的 OAuth 回调")
            return RedirectResponse(
                url=(
                    f"{settings.FRONTEND_URL}/ad-accounts"
                    f"?oauth_result=error&platform=baidu&reason=missing_state"
                ),
                status_code=302,
            )
        logger.warning("百度 OAuth 回调未携带有效 state，使用降级租户 ID（仅开发环境）")
        tenant_id = "default_tenant"

    try:
        service = get_baidu_service()

        # ── 2. 用授权码换取 Token ───────────────────────────────────
        token_info = await service.exchange_token(code)
        service.set_tokens(token_info.access_token, token_info.refresh_token)

        logger.info("百度营销 Token 换取成功", tenant_id=tenant_id)

        # ── 3. 获取账户信息 ─────────────────────────────────────────
        try:
            account_info = await service.get_account_info(
                access_token=token_info.access_token
            )
            account_name = account_info.username or "百度营销广告账户"
            advertiser_id = account_info.user_id
            balance = account_info.balance
        except AdPlatformError:
            # 获取账户信息失败时用默认值
            advertiser_id = f"bd_{secrets.token_hex(8)}"
            account_name = "百度营销广告账户"
            balance = 0.0

        # ── 4. 幂等写入 AdAccount ───────────────────────────────────
        existing_query = select(AdAccount).where(
            AdAccount.tenant_id == tenant_id,
            AdAccount.platform == AdPlatform.BAIDU,
            AdAccount.account_id == str(advertiser_id),
        )
        existing_result = await db.execute(existing_query)
        ad_account = existing_result.scalar_one_or_none()

        if ad_account:
            ad_account.access_token = token_info.access_token
            ad_account.refresh_token = token_info.refresh_token
            ad_account.token_expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=token_info.expires_in
            )
            ad_account.balance = balance
            ad_account.status = AdAccountStatus.ACTIVE
            logger.info("百度营销账户 Token 已刷新", account_id=ad_account.id)
        else:
            ad_account = AdAccount(
                tenant_id=tenant_id,
                platform=AdPlatform.BAIDU,
                account_id=str(advertiser_id),
                account_name=account_name,
                access_token=token_info.access_token,
                refresh_token=token_info.refresh_token,
                token_expires_at=datetime.now(timezone.utc) + timedelta(
                    seconds=token_info.expires_in
                ),
                balance=balance,
                status=AdAccountStatus.ACTIVE,
            )
            db.add(ad_account)

        await db.commit()
        await db.refresh(ad_account)

        # ── 5. 立即触发 Celery 任务拉取 7 天历史数据 ──────────────
        try:
            from app.tasks.sync_ad_tasks import sync_ad_data_baidu

            sync_ad_data_baidu.delay(ad_account.id, days=7)

            await set_sync_status(
                account_id=ad_account.id,
                status_data={
                    "status": "running",
                    "progress": 0,
                    "synced_count": 0,
                    "error_msg": None,
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "finished_at": None,
                },
            )
            logger.info("百度营销已触发立即同步任务", account_id=ad_account.id)
        except Exception as celery_err:
            logger.warning(
                "百度营销立即同步任务触发失败",
                account_id=ad_account.id,
                error=str(celery_err),
            )

        # ── 6. 重定向到前端成功页 ───────────────────────────────────
        return RedirectResponse(
            url=(
                f"{settings.FRONTEND_URL}/ad-accounts"
                f"?oauth_result=success"
                f"&platform=baidu"
                f"&account_id={ad_account.id}"
                f"&account_name={account_name}"
            ),
            status_code=302,
        )

    except AdPlatformError as e:
        logger.error("百度营销 OAuth 处理失败", error=e.detail)
        return RedirectResponse(
            url=(
                f"{settings.FRONTEND_URL}/ad-accounts"
                f"?oauth_result=error&platform=baidu&reason={e.detail}"
            ),
            status_code=302,
        )
    except Exception as e:
        logger.error("百度营销 OAuth 未知异常", error=str(e))
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/ad-accounts?oauth_result=error&platform=baidu",
            status_code=302,
        )


# ============================================================
# 广告账户管理
# ============================================================

@router.get("/accounts", response_model=AdAccountListResponse, summary="广告账户列表")
async def list_ad_accounts(
    platform: Optional[str] = Query(None, description="平台筛选: juliang | baidu"),
    status_filter: Optional[str] = Query(None, alias="status", description="状态筛选"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取当前租户下的广告账户列表"""
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


@router.get("/accounts/{account_id}", response_model=AdAccountResponse, summary="广告账户详情")
async def get_ad_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取单个广告账户详情（含租户隔离）"""
    query = select(AdAccount).where(
        AdAccount.id == account_id,
        AdAccount.tenant_id == current_user["tenant_id"],
    )
    result = await db.execute(query)
    account = result.scalar_one_or_none()

    if not account:
        raise ResourceNotFoundError("广告账户", account_id)

    return AdAccountResponse.model_validate(account)


@router.delete("/accounts/{account_id}", summary="断开广告账户")
async def delete_ad_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """断开广告账户（软删除：标记为 SUSPENDED 状态）"""
    query = select(AdAccount).where(
        AdAccount.id == account_id,
        AdAccount.tenant_id == current_user["tenant_id"],
    )
    result = await db.execute(query)
    account = result.scalar_one_or_none()

    if not account:
        raise ResourceNotFoundError("广告账户", account_id)

    account.status = AdAccountStatus.SUSPENDED
    await db.commit()

    return {"message": "广告账户已断开"}


@router.post(
    "/accounts/{account_id}/sync",
    response_model=ManualSyncResponse,
    summary="手动触发广告数据同步",
)
async def manual_sync_ad_data(
    account_id: str,
    body: ManualSyncRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """手动触发指定广告账户的数据同步任务"""
    query = select(AdAccount).where(
        AdAccount.id == account_id,
        AdAccount.tenant_id == current_user["tenant_id"],
    )
    result = await db.execute(query)
    account = result.scalar_one_or_none()

    if not account:
        raise ResourceNotFoundError("广告账户", account_id)

    if account.platform == AdPlatform.JULIANG:
        from app.tasks.sync_ad_tasks import sync_ad_data_juliang
        task = sync_ad_data_juliang.delay(account_id, days=body.days)
    elif account.platform == AdPlatform.BAIDU:
        from app.tasks.sync_ad_tasks import sync_ad_data_baidu
        task = sync_ad_data_baidu.delay(account_id, days=body.days)
    else:
        raise ValidationError(detail=f"暂不支持平台 {account.platform} 的手动同步")

    # 写入 Redis 同步状态
    await set_sync_status(
        account_id=account_id,
        status_data={
            "status": "running",
            "progress": 0,
            "synced_count": 0,
            "error_msg": None,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": None,
        },
    )

    return ManualSyncResponse(
        task_id=task.id,
        message=f"已提交同步任务，预计需要 {body.days * 2} 分钟完成",
        estimated_completion=(
            datetime.now(timezone.utc) + timedelta(minutes=body.days * 2)
        ).isoformat(),
    )


# ============================================================
# 同步状态查询（仪表盘空态判定）
# ============================================================

@router.get("/sync-status", response_model=SyncStatusResponse, summary="广告同步状态")
async def get_sync_status_api(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    获取当前租户广告同步状态，供仪表盘空态场景判定使用。

    返回字段：
      - ad_accounts_bound: 是否已绑定广告账户
      - has_ad_data:       是否已有广告数据
      - sync_in_progress:  是否有同步任务正在进行
      - last_sync_at:      最后同步完成时间
      - sync_error:        最近同步的错误信息（如有）
    """
    # 1. 检查是否绑定广告账户
    accounts_query = select(AdAccount).where(
        AdAccount.tenant_id == current_user["tenant_id"],
        AdAccount.status == AdAccountStatus.ACTIVE,
    )
    accounts_result = await db.execute(accounts_query)
    accounts = accounts_result.scalars().all()

    ad_accounts_bound = len(accounts) > 0

    # 2. 检查是否有广告数据
    has_ad_data = False
    if ad_accounts_bound:
        from app.models.ad_daily_stat import AdDailyStat

        data_query = (
            select(AdDailyStat)
            .where(AdDailyStat.tenant_id == current_user["tenant_id"])
            .limit(1)
        )
        data_result = await db.execute(data_query)
        has_ad_data = data_result.scalar_one_or_none() is not None

    # 3. 从 Redis 读取各账户同步状态
    sync_in_progress = False
    last_sync_at = None
    sync_error = None

    for account in accounts:
        status_data = await get_sync_status(account.id)
        if status_data:
            if status_data.get("status") == "running":
                sync_in_progress = True
            if status_data.get("finished_at") and not sync_in_progress:
                last_sync_at = status_data["finished_at"]
            if status_data.get("error_msg"):
                sync_error = status_data["error_msg"]

    return SyncStatusResponse(
        ad_accounts_bound=ad_accounts_bound,
        has_ad_data=has_ad_data,
        sync_in_progress=sync_in_progress,
        last_sync_at=last_sync_at,
        sync_error=sync_error,
    )

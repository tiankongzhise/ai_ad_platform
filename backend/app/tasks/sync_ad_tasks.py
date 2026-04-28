"""
广告数据同步 Celery 任务
包含立即拉取模式（绑定后）和定时拉取模式
"""
import structlog
from datetime import datetime, timedelta

from sqlalchemy import select

from app.core.database import get_db_context
from app.models.ad_account import AdAccount, AdAccountStatus, AdPlatform
from app.models.ad_daily_stat import AdDailyStat
from app.services.juliang_service import get_juliang_service
from app.tasks.celery_app import celery_app


logger = structlog.get_logger()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def sync_ad_data_juliang(self, account_id: str, days: int = 7):
    """
    同步巨量引擎广告数据
    
    Args:
        account_id: 广告账户 ID
        days: 同步天数，默认 7 天（立即拉取模式）
               定时任务使用 1-2 天
    
    触发场景:
    1. OAuth 回调后立即拉取（days=7） - 解决 UX BP-3
    2. Celery Beat 每日定时拉取（days=1 或 2）
    """
    logger.info(
        "开始同步巨量引擎广告数据",
        task_id=self.request.id,
        account_id=account_id,
        days=days,
    )
    
    try:
        # 获取广告账户信息
        with get_db_context() as db:
            query = select(AdAccount).where(AdAccount.id == account_id)
            result = db.execute(query)
            account = result.scalar_one_or_none()
            
            if not account:
                logger.error("广告账户不存在", account_id=account_id)
                return {"status": "error", "message": "广告账户不存在"}
            
            if account.platform != AdPlatform.JULIANG:
                logger.error("非巨量引擎账户", account_id=account_id)
                return {"status": "error", "message": "非巨量引擎账户"}
            
            # 检查 Token 有效性
            if not account.is_token_valid:
                logger.warning("Token 已过期，尝试刷新", account_id=account_id)
                # TODO: 实现 Token 刷新逻辑
                account.status = AdAccountStatus.EXPIRED
                db.commit()
                return {"status": "error", "message": "Token 已过期"}
            
            service = get_juliang_service()
            service.set_tokens(
                access_token=account.access_token,
                refresh_token=account.refresh_token,
            )
            
            # 获取广告数据
            advertiser_id = account.account_id
            
            # 处理可能的大数字 ID（巨量引擎有时返回较大数字）
            try:
                int_advertiser_id = int(advertiser_id)
            except ValueError:
                int_advertiser_id = advertiser_id
            
            # 调用巨量引擎 API 获取数据
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            stats = loop.run_until_complete(
                service.get_daily_stats(
                    advertiser_id=str(int_advertiser_id),
                    days=days,
                )
            )
            
            logger.info("获取到广告数据", count=len(stats), account_id=account_id)
            
            # 写入数据库
            synced_count = 0
            for stat in stats:
                # 检查是否已存在（去重）
                existing = db.execute(
                    select(AdDailyStat).where(
                        AdDailyStat.ad_account_id == account_id,
                        AdDailyStat.campaign_id == str(stat.campaign_id),
                        AdDailyStat.stat_date == datetime.strptime(stat.date, "%Y-%m-%d").date(),
                    )
                ).scalar_one_or_none()
                
                if existing:
                    # 更新已有记录
                    existing.impressions = stat.impressions
                    existing.clicks = stat.clicks
                    existing.spend = int(stat.spend * 100)  # 元转分
                    existing.form_submissions = stat.form_submit
                    existing.updated_at = datetime.now()
                else:
                    # 创建新记录
                    daily_stat = AdDailyStat(
                        tenant_id=account.tenant_id,
                        ad_account_id=account_id,
                        platform="juliang",
                        stat_date=datetime.strptime(stat.date, "%Y-%m-%d").date(),
                        campaign_id=str(stat.campaign_id),
                        campaign_name=stat.campaign_name,
                        impressions=stat.impressions,
                        clicks=stat.clicks,
                        spend=int(stat.spend * 100),  # 元转分存储
                        form_submissions=stat.form_submit,
                        cost_per_click=int(stat.cpc * 100) if stat.cpc else None,
                        ctr=stat.ctr,
                    )
                    db.add(daily_stat)
                
                synced_count += 1
            
            db.commit()
            
            logger.info(
                "巨量引擎广告数据同步完成",
                account_id=account_id,
                synced_count=synced_count,
            )
            
            return {
                "status": "success",
                "account_id": account_id,
                "synced_count": synced_count,
                "days": days,
            }
            
    except Exception as exc:
        logger.error(
            "巨量引擎广告数据同步失败",
            account_id=account_id,
            error=str(exc),
        )
        
        # 重试机制
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        
        return {
            "status": "error",
            "message": str(exc),
            "account_id": account_id,
        }


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def sync_ad_data_baidu(self, account_id: str, days: int = 1):
    """
    同步百度营销广告数据
    """
    logger.info(
        "开始同步百度营销广告数据",
        task_id=self.request.id,
        account_id=account_id,
        days=days,
    )
    
    # TODO: 实现百度营销 API 调用
    # 参考巨量引擎实现，使用类似的结构
    return {
        "status": "pending",
        "message": "百度营销同步待实现",
        "account_id": account_id,
    }


@celery_app.task
def daily_sync_juliang():
    """
    每日定时同步所有巨量引擎账户
    Celery Beat 调用
    """
    logger.info("开始每日巨量引擎定时同步")
    
    with get_db_context() as db:
        query = select(AdAccount).where(
            AdAccount.platform == AdPlatform.JULIANG,
            AdAccount.status == AdAccountStatus.ACTIVE,
        )
        result = db.execute(query)
        accounts = result.scalars().all()
        
        for account in accounts:
            # 同步最近 2 天数据（定时任务不需要拉取太多）
            sync_ad_data_juliang.delay(account.id, days=2)
        
        logger.info("已提交所有账户同步任务", count=len(accounts))
        
        return {"status": "success", "accounts_count": len(accounts)}


@celery_app.task
def daily_sync_baidu():
    """
    每日定时同步所有百度营销账户
    """
    logger.info("开始每日百度营销定时同步")
    
    # TODO: 实现
    return {"status": "pending", "message": "百度营销同步待实现"}


@celery_app.task(ignore_result=True)
def send_sync_failure_alert(account_id: str, error_message: str):
    """
    同步失败发送告警邮件
    """
    logger.warning(
        "广告同步失败",
        account_id=account_id,
        error=error_message,
    )
    
    # TODO: 实现邮件发送
    # from app.utils.email import send_alert_email
    # send_alert_email(...)
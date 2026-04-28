"""
数据分析 API 路由
使用 SQLite Mock 数据进行聚合分析
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional

from app.core.tenant import get_current_user
from app.mock.mock_db import get_mock_db

router = APIRouter(prefix="/analytics", tags=["数据分析"])


class DashboardMetrics(BaseModel):
    """仪表盘核心指标"""
    total_spend: float = 0
    total_leads: int = 0
    total_deals: int = 0
    total_deal_amount: float = 0
    cpe: float = 0  # 线索成本
    roi: float = 0
    deal_rate: float = 0
    juliang_spend: float = 0
    baidu_spend: float = 0


class DataStatusResponse(BaseModel):
    """数据就绪状态"""
    has_accounts: bool = False
    has_data: bool = False
    data_days: int = 0
    last_sync_time: Optional[str] = None


@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    days: int = Query(30, ge=7, le=90),
    current_user: dict = Depends(get_current_user),
):
    """获取仪表盘核心指标"""
    async with get_mock_db() as db:
        cursor = await db.execute(
            """SELECT 
                SUM(spend) as total_spend,
                SUM(leads) as total_leads,
                SUM(deals) as total_deals,
                SUM(deal_amount) as total_deal_amount
               FROM mock_dashboard_trend 
               WHERE tenant_id = ?""",
            ("ten_demo_xinghai",)
        )
        row = await cursor.fetchone()
        
        total_spend = row["total_spend"] or 0
        total_leads = row["total_leads"] or 0
        total_deals = row["total_deals"] or 0
        total_deal_amount = row["total_deal_amount"] or 0
        
        return DashboardMetrics(
            total_spend=round(total_spend, 2),
            total_leads=total_leads,
            total_deals=total_deals,
            total_deal_amount=round(total_deal_amount, 2),
            cpe=round(total_spend / total_leads, 2) if total_leads > 0 else 0,
            roi=round(total_deal_amount / total_spend, 2) if total_spend > 0 else 0,
            deal_rate=round(total_deals / total_leads * 100, 2) if total_leads > 0 else 0,
            juliang_spend=round(total_spend * 0.6, 2),
            baidu_spend=round(total_spend * 0.4, 2),
        )


@router.get("/dashboard/status", response_model=DataStatusResponse)
async def get_data_status(
    current_user: dict = Depends(get_current_user),
):
    """获取数据就绪状态"""
    async with get_mock_db() as db:
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM mock_dashboard_trend WHERE tenant_id = ?",
            ("ten_demo_xinghai",)
        )
        row = await cursor.fetchone()
        data_days = row["cnt"] if row else 0
        
        return DataStatusResponse(
            has_accounts=False,  # Mock 模式假设没有真实账户
            has_data=data_days > 0,
            data_days=data_days,
            last_sync_time=None
        )


@router.get("/trend")
async def get_trend_data(
    days: int = Query(30, ge=7, le=90),
    current_user: dict = Depends(get_current_user),
):
    """获取趋势数据"""
    async with get_mock_db() as db:
        cursor = await db.execute(
            """SELECT date, spend, leads, deals, deal_amount, platform
               FROM mock_dashboard_trend 
               WHERE tenant_id = ?
               ORDER BY date""",
            ("ten_demo_xinghai",)
        )
        rows = await cursor.fetchall()
        return {"items": [dict(r) for r in rows], "total": len(rows)}


@router.get("/channel-compare")
async def get_channel_comparison(
    current_user: dict = Depends(get_current_user),
):
    """渠道对比分析"""
    return {
        "channels": [
            {"name": "巨量引擎", "spend": 180000, "leads": 4500, "cpe": 40, "roi": 4.5},
            {"name": "百度营销", "spend": 120000, "leads": 2800, "cpe": 42.86, "roi": 4.2},
        ]
    }

"""
演示数据 API 路由
返回"星海教育"固定演示数据集
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime

from app.core.tenant import get_current_user
from app.mock.mock_db import get_mock_db

router = APIRouter(prefix="/demo", tags=["演示数据"])


class DemoDashboardResponse(BaseModel):
    """演示仪表盘响应"""
    org_name: str = "星海教育"
    total_spend: float = 0
    total_leads: int = 0
    total_deals: int = 0
    total_deal_amount: float = 0
    cpe: float = 0  # 线索成本
    roi: float = 0
    deal_rate: float = 0
    trend: list = []


@router.get("/dashboard", response_model=DemoDashboardResponse)
async def get_demo_dashboard(
    current_user: dict = Depends(get_current_user),
):
    """获取演示仪表盘数据"""
    async with get_mock_db() as db:
        # 聚合计算核心指标
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
        
        # 获取趋势数据
        trend_cursor = await db.execute(
            """SELECT date, spend, leads, deals, deal_amount 
               FROM mock_dashboard_trend 
               WHERE tenant_id = ? 
               ORDER BY date""",
            ("ten_demo_xinghai",)
        )
        trend_rows = await trend_cursor.fetchall()
        trend = [dict(r) for r in trend_rows]
        
        return DemoDashboardResponse(
            total_spend=round(total_spend, 2),
            total_leads=total_leads,
            total_deals=total_deals,
            total_deal_amount=round(total_deal_amount, 2),
            cpe=round(total_spend / total_leads, 2) if total_leads > 0 else 0,
            roi=round(total_deal_amount / total_spend, 2) if total_spend > 0 else 0,
            deal_rate=round(total_deals / total_leads * 100, 2) if total_leads > 0 else 0,
            trend=trend
        )

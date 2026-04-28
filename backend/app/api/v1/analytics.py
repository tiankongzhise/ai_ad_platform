"""
数据分析 API 路由
使用 SQLite Mock 数据进行聚合分析
"""
import secrets
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional

from app.core.tenant import get_current_user
from app.mock.mock_db import get_mock_db
from app.schemas.analytics import (
    DashboardMetrics,
    DashboardStatusResponse,
    TrendDataPoint,
    TrendResponse,
    ChannelCompareItem,
    ChannelCompareResponse,
    CrossTableRow,
    CrossTableResponse,
)

router = APIRouter(prefix="/analytics", tags=["数据分析"])


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


@router.get("/dashboard/status", response_model=DashboardStatusResponse)
async def get_data_status(
    current_user: dict = Depends(get_current_user),
):
    """获取数据就绪状态（仪表盘空态判定）"""
    async with get_mock_db() as db:
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM mock_dashboard_trend WHERE tenant_id = ?",
            ("ten_demo_xinghai",)
        )
        row = await cursor.fetchone()
        data_days = row["cnt"] if row else 0

        # 场景判定逻辑
        has_accounts = False  # Mock 模式假设没有真实账户
        has_data = data_days > 0

        if not has_accounts and not has_data:
            scenario = "scenario_a"  # 未绑定账户，无数据
        elif has_accounts and not has_data:
            scenario = "scenario_b"  # 已绑定账户，无数据
        elif has_data and not has_accounts:
            scenario = "scenario_c"  # 有数据但账户未绑定（Mock场景）
        else:
            scenario = "full_data"

        return DashboardStatusResponse(
            has_accounts=has_accounts,
            has_data=has_data,
            data_days=data_days,
            last_sync_time=None,
            scenario=scenario,
        )


@router.get("/trend", response_model=TrendResponse)
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
        items = [TrendDataPoint(
            date=str(r["date"]),
            spend=r["spend"],
            leads=r["leads"],
            deals=r["deals"],
            deal_amount=r["deal_amount"],
            platform=r.get("platform"),
        ) for r in rows]
        return TrendResponse(items=items, total=len(items))


@router.get("/channel-compare", response_model=ChannelCompareResponse)
async def get_channel_comparison(
    current_user: dict = Depends(get_current_user),
):
    """渠道对比分析"""
    return ChannelCompareResponse(
        channels=[
            ChannelCompareItem(
                name="巨量引擎",
                spend=180000,
                leads=4500,
                deals=180,
                deal_amount=810000,
                cpe=40,
                roi=4.5,
                deal_rate=4.0,
            ),
            ChannelCompareItem(
                name="百度营销",
                spend=120000,
                leads=2800,
                deals=112,
                deal_amount=504000,
                cpe=42.86,
                roi=4.2,
                deal_rate=4.0,
            ),
        ]
    )


@router.get("/cross-table", response_model=CrossTableResponse)
async def get_cross_table(
    dimension_a: str = Query("channel", description="维度A: channel | campaign"),
    dimension_b: str = Query("date", description="维度B: date | week"),
    days: int = Query(30, ge=7, le=90),
    current_user: dict = Depends(get_current_user),
):
    """
    交叉分析

    维度A（行展开）: channel(渠道) | campaign(计划)
    维度B（列展开）: date(日期) | week(周)
    """
    # Mock: 生成交叉分析数据
    mock_rows = [
        CrossTableRow(
            dimension_a="巨量引擎",
            dimension_b="2026-04-01",
            spend=6200, leads=155, deals=6, deal_amount=28000,
            cpe=40.0, roi=4.52,
        ),
        CrossTableRow(
            dimension_a="巨量引擎",
            dimension_b="2026-04-02",
            spend=5800, leads=145, deals=5, deal_amount=24000,
            cpe=40.0, roi=4.14,
        ),
        CrossTableRow(
            dimension_a="百度营销",
            dimension_b="2026-04-01",
            spend=4100, leads=96, deals=3, deal_amount=14400,
            cpe=42.71, roi=3.51,
        ),
        CrossTableRow(
            dimension_a="百度营销",
            dimension_b="2026-04-02",
            spend=3900, leads=91, deals=4, deal_amount=19200,
            cpe=42.86, roi=4.92,
        ),
    ]

    dim_a_label = "渠道" if dimension_a == "channel" else "计划"
    dim_b_label = "日期" if dimension_b == "date" else "周"

    return CrossTableResponse(
        dimension_a_label=dim_a_label,
        dimension_b_label=dim_b_label,
        rows=mock_rows,
        total=len(mock_rows),
    )


@router.get("/cross-table/export")
async def export_cross_table(
    dimension_a: str = Query("channel", description="维度A"),
    dimension_b: str = Query("date", description="维度B"),
    days: int = Query(30, ge=7, le=90),
    current_user: dict = Depends(get_current_user),
):
    """导出交叉分析为 CSV"""
    from fastapi.responses import StreamingResponse

    # Mock: 生成 CSV
    csv_content = "渠道,日期,花费,线索数,成交数,成交金额,线索成本,ROI\n"
    csv_content += "巨量引擎,2026-04-01,6200,155,6,28000,40.0,4.52\n"
    csv_content += "巨量引擎,2026-04-02,5800,145,5,24000,40.0,4.14\n"
    csv_content += "百度营销,2026-04-01,4100,96,3,14400,42.71,3.51\n"
    csv_content += "百度营销,2026-04-02,3900,91,4,19200,42.86,4.92\n"

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=cross_table_{dimension_a}_{dimension_b}.csv"
        },
    )

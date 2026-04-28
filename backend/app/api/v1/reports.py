"""
报表 API 路由
使用 SQLite Mock 数据生成报表
"""
from datetime import datetime
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List

from app.core.tenant import get_current_user
from app.mock.mock_db import get_mock_db

router = APIRouter(prefix="/reports", tags=["报表"])


class ReportResponse(BaseModel):
    """报表响应"""
    id: str
    tenant_id: str
    report_type: str
    date_range_start: str
    date_range_end: str
    status: str
    insights: Optional[List[str]] = None


@router.post("/generate")
async def generate_report(
    report_type: str,
    date_range_start: str,
    date_range_end: str,
    current_user: dict = Depends(get_current_user),
):
    """生成报表"""
    import secrets
    report_id = f"report_{secrets.token_hex(8)}"
    
    async with get_mock_db() as db:
        insights = '["建议增加抖音短视频投放预算", "百度关键词ROI下降"]'
        await db.execute(
            """INSERT INTO mock_reports
               (id, tenant_id, report_type, date_range_start, date_range_end,
                status, insights, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                report_id,
                current_user["tenant_id"],
                report_type,
                date_range_start,
                date_range_end,
                "ready",
                insights,
                datetime.now().isoformat()
            )
        )
        await db.commit()
    
    return {
        "report_id": report_id,
        "status": "ready",
        "message": "报表生成完成"
    }


@router.get("")
async def list_reports(
    current_user: dict = Depends(get_current_user),
):
    """报表列表"""
    async with get_mock_db() as db:
        cursor = await db.execute(
            "SELECT * FROM mock_reports WHERE tenant_id = ? ORDER BY created_at DESC",
            (current_user["tenant_id"],)
        )
        rows = await cursor.fetchall()
        return {"items": [dict(r) for r in rows], "total": len(rows)}


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
):
    """获取报表详情"""
    async with get_mock_db() as db:
        cursor = await db.execute(
            "SELECT * FROM mock_reports WHERE id = ? AND tenant_id = ?",
            (report_id, current_user["tenant_id"])
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return {"error": "报表不存在"}


@router.get("/{report_id}/insights")
async def get_report_insights(
    report_id: str,
    current_user: dict = Depends(get_current_user),
):
    """获取行动建议"""
    async with get_mock_db() as db:
        cursor = await db.execute(
            "SELECT insights FROM mock_reports WHERE id = ? AND tenant_id = ?",
            (report_id, current_user["tenant_id"])
        )
        row = await cursor.fetchone()
        if row and row["insights"]:
            import json
            try:
                insights = json.loads(row["insights"])
                return {"insights": insights}
            except:
                return {"insights": [row["insights"]]}
        return {"insights": []}


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
):
    """下载报表"""
    # Mock: 返回 CSV 格式的示例数据
    csv_content = "日期,花费,线索数,成交数,成交金额\n"
    csv_content += "2026-04-01,8500,210,38,190000\n"
    csv_content += "2026-04-02,9200,230,41,205000\n"
    
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=report_{report_id}.csv"}
    )

"""
报表 Schema
包含报表生成、列表、详情、行动建议等
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class GenerateReportRequest(BaseModel):
    """生成报表请求"""
    report_type: str = Field(..., description="报表类型: weekly | monthly | campaign | channel | custom")
    date_range_start: str = Field(..., description="开始日期 YYYY-MM-DD")
    date_range_end: str = Field(..., description="结束日期 YYYY-MM-DD")


class GenerateReportResponse(BaseModel):
    """生成报表响应"""
    report_id: str
    status: str = "generating"
    message: str = "报表生成中"


class InsightCard(BaseModel):
    """行动建议卡片"""
    title: str
    description: str
    priority: str = "medium"  # high | medium | low
    action: Optional[str] = None
    metric_change: Optional[float] = None


class ReportResponse(BaseModel):
    """报表响应"""
    id: str
    tenant_id: str
    report_type: str
    title: Optional[str] = None
    date_range_start: str
    date_range_end: str
    status: str
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    """报表列表响应"""
    items: list[ReportResponse]
    total: int


class ReportInsightsResponse(BaseModel):
    """行动建议响应"""
    report_id: str
    insights: list[InsightCard]


class ReportDownloadResponse(BaseModel):
    """报表下载响应"""
    download_url: str
    filename: str
    content_type: str = "text/csv"

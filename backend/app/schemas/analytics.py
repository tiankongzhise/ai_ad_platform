"""
数据分析 Schema
包含仪表盘指标、数据状态、趋势、渠道对比、交叉分析等
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================
# 仪表盘核心指标
# ============================================================

class DashboardMetrics(BaseModel):
    """仪表盘核心指标"""
    total_spend: float = 0
    total_leads: int = 0
    total_deals: int = 0
    total_deal_amount: float = 0
    cpe: float = Field(default=0, description="线索成本 (Cost Per Lead)")
    roi: float = Field(default=0, description="投资回报率")
    deal_rate: float = Field(default=0, description="成交率 (%)")
    juliang_spend: float = 0
    baidu_spend: float = 0


class DashboardStatusResponse(BaseModel):
    """数据就绪状态（用于仪表盘空态判定）"""
    has_accounts: bool = False
    has_data: bool = False
    data_days: int = 0
    last_sync_time: Optional[str] = None
    # 前端需要的场景标识
    scenario: Optional[str] = None  # scenario_a | scenario_b | scenario_c | full_data


# ============================================================
# 趋势数据
# ============================================================

class TrendDataPoint(BaseModel):
    """趋势数据点"""
    date: str
    spend: float = 0
    leads: int = 0
    deals: int = 0
    deal_amount: float = 0
    platform: Optional[str] = None


class TrendResponse(BaseModel):
    """趋势数据响应"""
    items: list[TrendDataPoint]
    total: int


# ============================================================
# 渠道对比
# ============================================================

class ChannelCompareItem(BaseModel):
    """渠道对比项"""
    name: str
    spend: float = 0
    leads: int = 0
    deals: int = 0
    cpe: float = 0
    roi: float = 0
    deal_rate: float = 0


class ChannelCompareResponse(BaseModel):
    """渠道对比响应"""
    channels: list[ChannelCompareItem]


# ============================================================
# 交叉分析
# ============================================================

class CrossTableRow(BaseModel):
    """交叉分析行"""
    dimension_a: str = Field(..., description="维度A值（如渠道名）")
    dimension_b: str = Field(..., description="维度B值（如日期）")
    spend: float = 0
    leads: int = 0
    deals: int = 0
    deal_amount: float = 0
    cpe: float = 0
    roi: float = 0


class CrossTableResponse(BaseModel):
    """交叉分析响应"""
    dimension_a_label: str = "渠道"
    dimension_b_label: str = "日期"
    rows: list[CrossTableRow]
    total: int


class CrossTableExportResponse(BaseModel):
    """交叉分析导出响应"""
    download_url: str
    filename: str

"""
广告每日数据统计模型
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AdDailyStat(Base):
    """广告每日数据统计表"""
    __tablename__ = "ad_daily_stats"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # 租户关联
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True
    )
    
    # 广告账户关联
    ad_account_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ad_accounts.id"),
        nullable=False,
        index=True
    )
    
    # 平台
    platform: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True
    )
    
    # 日期
    stat_date: Mapped[datetime] = mapped_column(
        Date,
        nullable=False,
        index=True
    )
    
    # 计划层级
    campaign_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True
    )
    campaign_name: Mapped[str] = mapped_column(
        String(512),
        nullable=False
    )
    
    # 单元层级（可选）
    adgroup_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True
    )
    adgroup_name: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True
    )
    
    # 核心指标
    spend: Mapped[int] = mapped_column(
        Integer,
        default=0,  # 实际存储单位：分
        nullable=False
    )
    impressions: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    clicks: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    form_submissions: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    
    # 计算指标
    cost_per_click: Mapped[Optional[float]] = mapped_column(
        Numeric(18, 2),
        nullable=True
    )
    cost_per_form: Mapped[Optional[float]] = mapped_column(
        Numeric(18, 2),
        nullable=True
    )
    ctr: Mapped[Optional[float]] = mapped_column(
        nullable=True
    )  # 点击率
    cvr: Mapped[Optional[float]] = mapped_column(
        nullable=True
    )  # 转化率
    
    # 同步状态
    sync_status: Mapped[str] = mapped_column(
        String(32),
        default="synced",
        nullable=False
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False
    )
    
    # 索引
    __table_args__ = (
        Index("idx_tenant_date", "tenant_id", "stat_date"),
        Index("idx_account_date", "ad_account_id", "stat_date"),
        Index("idx_tenant_campaign", "tenant_id", "campaign_id", "stat_date"),
    )
    
    @property
    def spend_yuan(self) -> float:
        """花费（转换为元）"""
        return self.spend / 100
    
    def __repr__(self) -> str:
        return f"<AdDailyStat(campaign={self.campaign_name}, date={self.stat_date})>"

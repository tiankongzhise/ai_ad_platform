"""
CRM 线索 ORM 模型
存储从 Excel 导入的客户线索数据
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CRMLead(Base):
    """CRM 线索表"""
    __tablename__ = "crm_leads"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    # 租户关联
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    # 导入批次关联
    batch_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("crm_import_batches.id"),
        nullable=False,
        index=True,
    )

    # 线索基本信息
    name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        index=True,
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # 原始数据（Excel 行的完整 JSON）
    raw_data: Mapped[Optional[dict]] = mapped_column(
        Text,
        nullable=True,
        comment="原始 Excel 行数据 JSON",
    )

    # 归因信息
    attribution_status: Mapped[str] = mapped_column(
        String(32),
        default="pending",
        nullable=False,
        comment="pending | attributed | manual | unmatched",
    )
    attributed_ad_account_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("ad_accounts.id"),
        nullable=True,
    )
    attributed_campaign_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )
    attribution_rule_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        comment="匹配到的归因规则 ID",
    )
    attribution_confidence: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="归因置信度 0-1",
    )

    # 线索状态
    lead_status: Mapped[str] = mapped_column(
        String(32),
        default="new",
        nullable=False,
        comment="new | contacted | qualified | converted | lost",
    )
    deal_amount: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="成交金额",
    )
    deal_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    # 备注
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<CRMLead(id={self.id}, name={self.name}, status={self.lead_status})>"

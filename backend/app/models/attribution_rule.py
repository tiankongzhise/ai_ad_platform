"""
归因规则 ORM 模型
定义线索到广告渠道的归因匹配规则
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RuleMatchMode(str, enum.Enum):
    """规则匹配模式"""
    EXACT = "exact"            # 精确匹配
    CONTAINS = "contains"      # 包含匹配
    REGEX = "regex"            # 正则匹配
    FUZZY = "fuzzy"            # 模糊匹配


class AttributionRule(Base):
    """归因规则表"""
    __tablename__ = "attribution_rules"

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

    # 规则基本信息
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="规则名称",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # 目标平台
    platform: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="juliang | baidu | all",
    )

    # 匹配条件
    match_field: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="phone",
        comment="匹配字段: phone | name | utm_source | custom",
    )
    match_mode: Mapped[RuleMatchMode] = mapped_column(
        Enum(RuleMatchMode),
        default=RuleMatchMode.CONTAINS,
        nullable=False,
    )
    keywords: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="匹配关键词列表",
    )

    # 目标广告账户
    target_ad_account_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("ad_accounts.id"),
        nullable=True,
    )

    # 优先级（数值越大优先级越高）
    priority: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # 是否启用
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
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
        return f"<AttributionRule(id={self.id}, name={self.name}, priority={self.priority})>"

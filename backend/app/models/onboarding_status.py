"""
引导状态 ORM 模型
记录租户的 3 步引导向导完成进度
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class OnboardingStatus(Base):
    """引导状态表"""
    __tablename__ = "onboarding_status"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    # 租户关联（一对一）
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Step 1: 基础信息（机构名称、行业）
    step1_done: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    step1_org_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    step1_industry: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )

    # Step 2: 广告账户绑定
    step2_done: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Step 3: CRM 数据导入
    step3_done: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # 总完成状态
    completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
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
        return f"<OnboardingStatus(tenant={self.tenant_id}, completed={self.completed})>"

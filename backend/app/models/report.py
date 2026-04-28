"""
报表 ORM 模型
存储 AI 生成的分析报表和行动建议
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ReportType(str, enum.Enum):
    """报表类型"""
    WEEKLY = "weekly"          # 周报
    MONTHLY = "monthly"        # 月报
    CAMPAIGN = "campaign"      # 广告计划报告
    CHANNEL = "channel"        # 渠道对比报告
    CUSTOM = "custom"          # 自定义


class ReportStatus(str, enum.Enum):
    """报表状态"""
    GENERATING = "generating"  # 生成中
    READY = "ready"            # 已完成
    FAILED = "failed"          # 生成失败


class Report(Base):
    """报表表"""
    __tablename__ = "reports"

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

    # 报表基本信息
    report_type: Mapped[ReportType] = mapped_column(
        Enum(ReportType),
        nullable=False,
    )
    title: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="报表标题",
    )

    # 时间范围
    date_range_start: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
    date_range_end: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    # 状态
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus),
        default=ReportStatus.GENERATING,
        nullable=False,
    )

    # 报表内容
    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="报表摘要",
    )
    insights: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="行动建议 JSON 数组",
    )
    data_snapshot: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="报表数据快照 JSON",
    )

    # 文件存储
    file_path: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="生成的报表文件路径",
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
        return f"<Report(id={self.id}, type={self.report_type}, status={self.status})>"

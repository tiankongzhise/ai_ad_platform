"""
CRM 导入批次 ORM 模型
记录 Excel 文件上传和处理的批次信息
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ImportBatchStatus(str, enum.Enum):
    """导入批次状态"""
    UPLOADING = "uploading"        # 上传中
    PROCESSING = "processing"      # 解析中
    AWAITING_MAPPING = "awaiting_mapping"  # 等待字段映射确认
    AWAITING_ATTRIBUTION = "awaiting_attribution"  # 等待归因确认
    IMPORTING = "importing"        # 导入中
    COMPLETED = "completed"        # 完成
    FAILED = "failed"             # 失败


class CRMImportBatch(Base):
    """CRM 导入批次表"""
    __tablename__ = "crm_import_batches"

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

    # 文件信息
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    file_path: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="文件存储路径",
    )
    file_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="文件大小（字节）",
    )

    # 处理状态
    status: Mapped[ImportBatchStatus] = mapped_column(
        Enum(ImportBatchStatus),
        default=ImportBatchStatus.UPLOADING,
        nullable=False,
    )

    # 数据统计
    total_rows: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="总行数",
    )
    processed_rows: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="已处理行数",
    )
    success_rows: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="成功导入行数",
    )
    failed_rows: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="失败行数",
    )

    # 字段映射（JSON 字符串）
    field_mapping: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="字段映射配置 JSON",
    )

    # 错误信息
    error_message: Mapped[Optional[str]] = mapped_column(
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
        return f"<CRMImportBatch(id={self.id}, status={self.status})>"

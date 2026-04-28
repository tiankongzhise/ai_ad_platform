"""
租户（用户组织）模型
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Tenant(Base):
    """租户表"""
    __tablename__ = "tenants"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: f"ten_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    )
    
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    # 行业子类（如：K12、职业教育、语言培训等）
    industry_sub_type: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True
    )
    
    # 主营产品/课程
    main_product: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    
    # 额外配置
    settings: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True
    )
    
    # 状态
    is_active: Mapped[bool] = mapped_column(
        default=True,
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
    
    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name={self.name})>"

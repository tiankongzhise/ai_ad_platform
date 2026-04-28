"""
用户模型
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: f"usr_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    )
    
    # 租户关联
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True
    )
    
    # 基本信息
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    # 个人资料
    name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    
    # 角色
    role: Mapped[str] = mapped_column(
        String(32),
        default="member",  # admin | manager | member
        nullable=False
    )
    
    # 状态
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False
    )
    email_verified: Mapped[bool] = mapped_column(
        default=False,
        nullable=False
    )
    
    # 微信小程序 OpenID（可选）
    wx_openid: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        unique=True
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
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"

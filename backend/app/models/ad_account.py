"""
广告账户模型
巨量引擎/百度营销 OAuth 授权信息
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AdPlatform(str, enum.Enum):
    """广告平台枚举"""
    JULIANG = "juliang"      # 巨量引擎（抖音）
    BAIDU = "baidu"          # 百度营销


class AdAccountStatus(str, enum.Enum):
    """广告账户状态"""
    ACTIVE = "active"        # 正常
    SUSPENDED = "suspended"   # 暂停
    AUTHORIZED = "authorized" # 已授权（待激活）
    EXPIRED = "expired"      # Token过期
    ERROR = "error"          # 异常


class AdAccount(Base):
    """广告账户表"""
    __tablename__ = "ad_accounts"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: f"ada_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    )
    
    # 租户关联
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True
    )
    
    # 平台信息
    platform: Mapped[AdPlatform] = mapped_column(
        Enum(AdPlatform),
        nullable=False,
        index=True
    )
    
    # 平台返回的账户ID（巨量引擎的 advertiser_id）
    account_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True
    )
    account_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    # OAuth Token 信息
    access_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    refresh_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    
    # 账户余额（仅展示）
    balance: Mapped[Optional[float]] = mapped_column(
        BigInteger,
        nullable=True,
        default=0
    )
    
    # 状态
    status: Mapped[AdAccountStatus] = mapped_column(
        Enum(AdAccountStatus),
        default=AdAccountStatus.AUTHORIZED,
        nullable=False
    )
    
    # 额外信息（JSON）
    extra_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True
    )
    
    # 关联关系
    # tenant = relationship("Tenant", back_populates="ad_accounts")
    # daily_stats = relationship("AdDailyStat", back_populates="ad_account")
    
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
        return f"<AdAccount(id={self.id}, platform={self.platform}, name={self.account_name})>"
    
    @property
    def is_token_valid(self) -> bool:
        """Token是否有效"""
        if not self.token_expires_at:
            return False
        # 提前10分钟判定为过期
        from datetime import timedelta
        return datetime.now() < (self.token_expires_at - timedelta(minutes=10))

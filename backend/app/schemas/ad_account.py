"""
广告账户 Schema
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AdAccountBase(BaseModel):
    """广告账户基础模型"""
    account_id: str = Field(..., description="广告平台账户ID")
    account_name: str = Field(..., description="广告账户名称")
    platform: str = Field(..., description="平台类型: juliang | baidu")


class AdAccountCreate(AdAccountBase):
    """创建广告账户"""
    pass


class AdAccountUpdate(BaseModel):
    """更新广告账户"""
    account_name: Optional[str] = None
    status: Optional[str] = None


class AdAccountResponse(AdAccountBase):
    """广告账户响应"""
    id: str
    tenant_id: str
    balance: Optional[float] = 0
    status: str
    token_expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class AdAccountListResponse(BaseModel):
    """广告账户列表响应"""
    items: list[AdAccountResponse]
    total: int


class OAuthCallbackRequest(BaseModel):
    """OAuth 回调请求"""
    code: str = Field(..., description="授权码")
    state: Optional[str] = Field(None, description="状态参数")


class OAuthCallbackResponse(BaseModel):
    """OAuth 回调响应"""
    status: str = "success"
    ad_account_id: str
    account_name: str
    next_step: str = "crm_import"  # 引导向导下一步
    message: str = "巨量引擎授权成功"


class SyncStatusResponse(BaseModel):
    """广告同步状态响应"""
    ad_accounts_bound: bool = False
    has_ad_data: bool = False
    sync_in_progress: bool = False
    last_sync_at: Optional[datetime] = None
    sync_error: Optional[str] = None


class ManualSyncRequest(BaseModel):
    """手动同步请求"""
    days: int = Field(default=7, ge=1, le=90, description="同步天数")


class ManualSyncResponse(BaseModel):
    """手动同步响应"""
    task_id: str
    message: str
    estimated_completion: str  # ISO datetime

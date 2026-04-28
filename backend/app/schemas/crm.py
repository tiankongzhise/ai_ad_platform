"""
CRM Schema
包含文件上传、字段映射、线索列表、归因建议等
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================
# 文件上传
# ============================================================

class UploadResponse(BaseModel):
    """文件上传响应"""
    batch_id: str
    task_id: str
    message: str


class UploadProgressResponse(BaseModel):
    """上传进度响应"""
    task_id: str
    status: str  # uploading | processing | completed | failed
    progress: int = Field(ge=0, le=100)
    total_rows: Optional[int] = None
    processed_rows: Optional[int] = None
    message: str = ""


# ============================================================
# 字段映射
# ============================================================

class FieldMappingItem(BaseModel):
    """单个字段映射"""
    source_field: str = Field(..., description="Excel 源字段名")
    target_field: str = Field(..., description="系统目标字段名")
    confidence: float = Field(default=1.0, ge=0, le=1, description="映射置信度")
    sample_values: list[str] = Field(default_factory=list, description="示例值")


class FieldMappingResponse(BaseModel):
    """字段预览/映射响应"""
    batch_id: str
    total_rows: int = 0
    fields: list[FieldMappingItem] = []
    unmapped_fields: list[str] = []


class ConfirmMappingRequest(BaseModel):
    """确认字段映射请求"""
    mappings: list[FieldMappingItem] = Field(..., description="确认后的字段映射")


# ============================================================
# 归因建议
# ============================================================

class AttributionSuggestion(BaseModel):
    """归因建议"""
    lead_id: str
    lead_name: Optional[str] = None
    lead_phone: Optional[str] = None
    suggested_platform: str  # juliang | baidu | unmatched
    suggested_ad_account_id: Optional[str] = None
    suggested_campaign_name: Optional[str] = None
    confidence: float = 0.0
    match_rule: Optional[str] = None  # 匹配的规则名


class AttributionSuggestResponse(BaseModel):
    """归因建议响应"""
    batch_id: str
    total_leads: int = 0
    attributed_count: int = 0
    unmatched_count: int = 0
    suggestions: list[AttributionSuggestion] = []


class ConfirmAttributionRequest(BaseModel):
    """确认归因请求"""
    accept_all: bool = False
    manual_mappings: Optional[list[dict]] = None  # 手动指定映射


# ============================================================
# 线索
# ============================================================

class CRMLeadResponse(BaseModel):
    """线索响应"""
    id: str
    tenant_id: str
    batch_id: str
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    lead_status: str = "new"
    attribution_status: str = "pending"
    attributed_ad_account_id: Optional[str] = None
    deal_amount: Optional[float] = None
    deal_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CRMLeadUpdateRequest(BaseModel):
    """线索更新请求"""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    lead_status: Optional[str] = None
    attribution_status: Optional[str] = None
    deal_amount: Optional[float] = None
    deal_date: Optional[datetime] = None
    notes: Optional[str] = None


class CRMLeadListResponse(BaseModel):
    """线索列表响应"""
    items: list[CRMLeadResponse]
    total: int
    page: int = 1
    page_size: int = 20


# ============================================================
# 批次
# ============================================================

class CRMImportBatchResponse(BaseModel):
    """导入批次响应"""
    id: str
    tenant_id: str
    filename: str
    status: str
    total_rows: Optional[int] = None
    success_rows: Optional[int] = None
    failed_rows: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CRMImportBatchListResponse(BaseModel):
    """导入批次列表响应"""
    items: list[CRMImportBatchResponse]
    total: int

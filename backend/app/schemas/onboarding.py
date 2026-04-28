"""
引导向导 Schema
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class OnboardingStatusResponse(BaseModel):
    """引导状态响应"""
    step1_done: bool = False
    step1_org_name: Optional[str] = None
    step1_industry: Optional[str] = None
    step2_done: bool = False
    step3_done: bool = False
    completed: bool = False
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UpdateOnboardingRequest(BaseModel):
    """更新引导请求"""
    step1_done: Optional[bool] = None
    step1_org_name: Optional[str] = None
    step1_industry: Optional[str] = None
    step2_done: Optional[bool] = None
    step3_done: Optional[bool] = None


class CompleteOnboardingResponse(BaseModel):
    """完成引导响应"""
    message: str = "引导已完成"
    completed: bool = True

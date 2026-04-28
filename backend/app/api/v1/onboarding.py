"""
引导向导 API 路由
使用 SQLite Mock 存储引导进度
"""
from datetime import datetime
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.tenant import get_current_user
from app.mock.mock_db import get_mock_db

router = APIRouter(prefix="/onboarding", tags=["引导向导"])


class OnboardingStatusResponse(BaseModel):
    """引导状态响应"""
    step1_done: bool = False
    step1_org_name: str = None
    step1_industry: str = None
    step2_done: bool = False
    step3_done: bool = False
    completed: bool = False


class UpdateOnboardingRequest(BaseModel):
    """更新引导请求"""
    step1_done: bool = None
    step1_org_name: str = None
    step1_industry: str = None


@router.get("/status", response_model=OnboardingStatusResponse)
async def get_onboarding_status(
    current_user: dict = Depends(get_current_user),
):
    """获取引导进度"""
    async with get_mock_db() as db:
        cursor = await db.execute(
            "SELECT * FROM mock_onboarding WHERE tenant_id = ?",
            (current_user["tenant_id"],)
        )
        row = await cursor.fetchone()
        
        if row:
            return OnboardingStatusResponse(
                step1_done=bool(row["step1_done"]),
                step1_org_name=row["step1_org_name"],
                step1_industry=row["step1_industry"],
                step2_done=bool(row["step2_done"]),
                step3_done=bool(row["step3_done"]),
                completed=all([
                    bool(row["step1_done"]),
                    bool(row["step2_done"]),
                    bool(row["step3_done"]),
                ])
            )
        
        return OnboardingStatusResponse()


@router.post("/status")
async def update_onboarding_status(
    body: UpdateOnboardingRequest,
    current_user: dict = Depends(get_current_user),
):
    """更新引导进度"""
    async with get_mock_db() as db:
        # UPSERT 逻辑
        await db.execute(
            """INSERT INTO mock_onboarding 
               (tenant_id, step1_done, step1_org_name, step1_industry, updated_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(tenant_id) DO UPDATE SET
               step1_done=excluded.step1_done,
               step1_org_name=excluded.step1_org_name,
               step1_industry=excluded.step1_industry,
               updated_at=excluded.updated_at""",
            (
                current_user["tenant_id"],
                1 if body.step1_done else 0,
                body.step1_org_name,
                body.step1_industry,
                datetime.now().isoformat()
            )
        )
        await db.commit()
    
    return {"message": "引导进度已更新"}


@router.post("/complete")
async def complete_onboarding(
    current_user: dict = Depends(get_current_user),
):
    """标记引导全部完成"""
    async with get_mock_db() as db:
        await db.execute(
            """UPDATE mock_onboarding 
               SET step1_done=1, step2_done=1, step3_done=1,
                   completed_at=?, updated_at=?
               WHERE tenant_id=?""",
            (datetime.now().isoformat(), datetime.now().isoformat(),
             current_user["tenant_id"])
        )
        await db.commit()
    
    return {"message": "引导已完成"}

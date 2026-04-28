"""
设置 API 路由
混合实现：租户信息用真实数据库，归因规则用 Mock
"""
from datetime import datetime
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List

from app.core.tenant import get_current_user
from app.mock.mock_db import get_mock_db

router = APIRouter(prefix="/settings", tags=["设置"])


class TenantInfo(BaseModel):
    """租户信息"""
    id: str
    name: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class AttributionRule(BaseModel):
    """归因规则"""
    id: str
    tenant_id: str
    name: str
    platform: str
    keywords: List[str]
    priority: int
    created_at: str


@router.get("/tenant", response_model=TenantInfo)
async def get_tenant_info(
    current_user: dict = Depends(get_current_user),
):
    """获取租户信息"""
    # 从 Mock 数据库获取（实际应从 MySQL）
    async with get_mock_db() as db:
        cursor = await db.execute(
            "SELECT * FROM mock_onboarding WHERE tenant_id = ?",
            (current_user["tenant_id"],)
        )
        row = await cursor.fetchone()
        if row:
            return TenantInfo(
                id=current_user["tenant_id"],
                name=row["step1_org_name"] or "星海教育",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        return TenantInfo(
            id=current_user["tenant_id"],
            name="未命名机构",
            created_at=datetime.now()
        )


@router.patch("/tenant")
async def update_tenant_info(
    name: str,
    current_user: dict = Depends(get_current_user),
):
    """更新租户信息"""
    async with get_mock_db() as db:
        await db.execute(
            """UPDATE mock_onboarding 
               SET step1_org_name = ?, updated_at = ?
               WHERE tenant_id = ?""",
            (name, datetime.now().isoformat(), current_user["tenant_id"])
        )
        await db.commit()
    return {"message": "租户信息已更新"}


@router.get("/attribution-rules")
async def list_attribution_rules(
    current_user: dict = Depends(get_current_user),
):
    """归因规则列表"""
    async with get_mock_db() as db:
        cursor = await db.execute(
            "SELECT * FROM mock_attribution_rules WHERE tenant_id = ? ORDER BY priority DESC",
            (current_user["tenant_id"],)
        )
        rows = await cursor.fetchall()
        return {"items": [dict(r) for r in rows], "total": len(rows)}


@router.post("/attribution-rules")
async def create_attribution_rule(
    name: str,
    platform: str,
    keywords: List[str],
    priority: int = 0,
    current_user: dict = Depends(get_current_user),
):
    """创建归因规则"""
    import secrets
    import json
    rule_id = f"attr_{secrets.token_hex(8)}"
    
    async with get_mock_db() as db:
        await db.execute(
            """INSERT INTO mock_attribution_rules
               (id, tenant_id, name, platform, keywords, priority, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                rule_id,
                current_user["tenant_id"],
                name,
                platform,
                json.dumps(keywords),
                priority,
                datetime.now().isoformat()
            )
        )
        await db.commit()
    
    return {"id": rule_id, "message": "归因规则已创建"}


@router.patch("/attribution-rules/{rule_id}")
async def update_attribution_rule(
    rule_id: str,
    name: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    priority: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
):
    """更新归因规则"""
    import json
    updates = []
    params = []
    
    if name:
        updates.append("name = ?")
        params.append(name)
    if keywords:
        updates.append("keywords = ?")
        params.append(json.dumps(keywords))
    if priority is not None:
        updates.append("priority = ?")
        params.append(priority)
    
    if updates:
        params.append(rule_id)
        params.append(current_user["tenant_id"])
        async with get_mock_db() as db:
            await db.execute(
                f"""UPDATE mock_attribution_rules 
                   SET {', '.join(updates)} 
                   WHERE id = ? AND tenant_id = ?""",
                params
            )
            await db.commit()
    
    return {"message": "归因规则已更新"}


@router.delete("/attribution-rules/{rule_id}")
async def delete_attribution_rule(
    rule_id: str,
    current_user: dict = Depends(get_current_user),
):
    """删除归因规则"""
    async with get_mock_db() as db:
        await db.execute(
            "DELETE FROM mock_attribution_rules WHERE id = ? AND tenant_id = ?",
            (rule_id, current_user["tenant_id"])
        )
        await db.commit()
    return {"message": "归因规则已删除"}

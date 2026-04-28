"""
CRM 导入 API 路由
混合实现：文件上传用真实，数据查询用 Mock
"""
import os
import secrets
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Query
from pydantic import BaseModel

from app.core.tenant import get_current_user
from app.mock.mock_db import get_mock_db

router = APIRouter(prefix="/crm", tags=["CRM 导入"])


class UploadResponse(BaseModel):
    """文件上传响应"""
    batch_id: str
    task_id: str
    message: str


class LeadsListResponse(BaseModel):
    """线索列表响应"""
    items: list = []
    total: int = 0
    page: int = 1
    page_size: int = 20


@router.post("/upload", response_model=UploadResponse)
async def upload_crm_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """上传 CRM Excel 文件"""
    # 保存文件到临时目录
    temp_dir = "/tmp/crm_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    
    file_path = os.path.join(temp_dir, f"{current_user['tenant_id']}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # 创建 Mock 批次记录
    batch_id = f"batch_{secrets.token_hex(8)}"
    async with get_mock_db() as db:
        await db.execute(
            """INSERT INTO mock_crm_batches 
               (id, tenant_id, filename, status, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (batch_id, current_user["tenant_id"], file.filename, 
             "processing", datetime.now().isoformat())
        )
        await db.commit()
    
    return UploadResponse(
        batch_id=batch_id,
        task_id=f"task_{secrets.token_hex(8)}",
        message="文件上传成功，正在处理..."
    )


@router.get("/upload/{task_id}")
async def get_upload_progress(
    task_id: str,
    current_user: dict = Depends(get_current_user),
):
    """获取上传处理进度"""
    # Mock 进度查询
    return {
        "task_id": task_id,
        "status": "completed",
        "progress": 100,
        "total_rows": 100,
        "processed_rows": 100,
        "message": "处理完成"
    }


@router.get("/leads", response_model=LeadsListResponse)
async def list_crm_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """线索列表（Mock）"""
    async with get_mock_db() as db:
        cursor = await db.execute(
            """SELECT * FROM mock_crm_leads 
               WHERE tenant_id = ? 
               LIMIT ? OFFSET ?""",
            (current_user["tenant_id"], page_size, (page-1)*page_size)
        )
        rows = await cursor.fetchall()
        leads = [dict(r) for r in rows]
        
        # 总数
        count_cursor = await db.execute(
            "SELECT COUNT(*) FROM mock_crm_leads WHERE tenant_id = ?",
            (current_user["tenant_id"],)
        )
        total = (await count_cursor.fetchone())[0]
        
        return LeadsListResponse(
            items=leads,
            total=total,
            page=page,
            page_size=page_size
        )


@router.get("/batches")
async def list_batches(
    current_user: dict = Depends(get_current_user),
):
    """批次列表"""
    async with get_mock_db() as db:
        cursor = await db.execute(
            "SELECT * FROM mock_crm_batches WHERE tenant_id = ? ORDER BY created_at DESC",
            (current_user["tenant_id"],)
        )
        rows = await cursor.fetchall()
        return {"items": [dict(r) for r in rows], "total": len(rows)}


@router.delete("/batches/{batch_id}")
async def delete_batch(
    batch_id: str,
    current_user: dict = Depends(get_current_user),
):
    """删除批次"""
    async with get_mock_db() as db:
        await db.execute(
            "DELETE FROM mock_crm_batches WHERE id = ? AND tenant_id = ?",
            (batch_id, current_user["tenant_id"])
        )
        await db.commit()
    return {"message": "批次已删除"}

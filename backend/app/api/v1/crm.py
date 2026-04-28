"""
CRM 导入 API 路由
混合实现：文件上传用真实，数据查询用 Mock
"""
import json
import os
import secrets
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Query
from pydantic import BaseModel

from app.core.config import settings
from app.core.tenant import get_current_user
from app.mock.mock_db import get_mock_db
from app.schemas.crm import (
    UploadResponse,
    UploadProgressResponse,
    FieldMappingItem,
    FieldMappingResponse,
    ConfirmMappingRequest,
    AttributionSuggestion,
    AttributionSuggestResponse,
    ConfirmAttributionRequest,
    CRMLeadResponse,
    CRMLeadUpdateRequest,
    CRMLeadListResponse,
    CRMImportBatchResponse,
    CRMImportBatchListResponse,
)

router = APIRouter(prefix="/crm", tags=["CRM 导入"])


@router.post("/upload", response_model=UploadResponse)
async def upload_crm_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """上传 CRM Excel 文件"""
    # 保存文件到配置的上传目录
    upload_dir = os.path.join(settings.LOCAL_STORAGE_PATH, "crm_uploads")
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, f"{current_user['tenant_id']}_{file.filename}")
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


@router.get("/upload/{task_id}", response_model=UploadProgressResponse)
async def get_upload_progress(
    task_id: str,
    current_user: dict = Depends(get_current_user),
):
    """获取上传处理进度"""
    # Mock 进度查询
    return UploadProgressResponse(
        task_id=task_id,
        status="completed",
        progress=100,
        total_rows=100,
        processed_rows=100,
        message="处理完成"
    )


@router.post("/upload/{batch_id}/preview", response_model=FieldMappingResponse)
async def preview_field_mapping(
    batch_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    预览字段映射（有副作用：触发服务端字段分析）

    HTTP Method 为 POST，因为预览操作需要在服务端触发字段分析（有副作用），
    不应使用 GET。
    """
    # Mock: 返回模拟的字段映射结果
    mock_fields = [
        FieldMappingItem(
            source_field="姓名",
            target_field="name",
            confidence=0.95,
            sample_values=["张三", "李四", "王五"],
        ),
        FieldMappingItem(
            source_field="手机号",
            target_field="phone",
            confidence=0.98,
            sample_values=["13800138000", "13900139000"],
        ),
        FieldMappingItem(
            source_field="邮箱",
            target_field="email",
            confidence=0.85,
            sample_values=["zhang@example.com"],
        ),
        FieldMappingItem(
            source_field="备注",
            target_field="notes",
            confidence=0.6,
            sample_values=["百度搜索", "抖音广告"],
        ),
    ]

    return FieldMappingResponse(
        batch_id=batch_id,
        total_rows=100,
        fields=mock_fields,
        unmapped_fields=["来源渠道", "意向等级"],
    )


@router.post("/upload/{batch_id}/confirm")
async def confirm_field_mapping(
    batch_id: str,
    body: ConfirmMappingRequest,
    current_user: dict = Depends(get_current_user),
):
    """确认字段映射"""
    async with get_mock_db() as db:
        # 更新批次状态为等待归因确认
        await db.execute(
            """UPDATE mock_crm_batches
               SET status = ?, field_mapping = ?
               WHERE id = ? AND tenant_id = ?""",
            (
                "awaiting_attribution",
                json.dumps([m.model_dump() for m in body.mappings]),
                batch_id,
                current_user["tenant_id"],
            )
        )
        await db.commit()

    return {
        "batch_id": batch_id,
        "status": "awaiting_attribution",
        "message": "字段映射已确认，请确认归因"
    }


@router.get("/upload/{batch_id}/attribution-suggest", response_model=AttributionSuggestResponse)
async def get_attribution_suggestions(
    batch_id: str,
    current_user: dict = Depends(get_current_user),
):
    """获取归因建议"""
    # Mock: 返回模拟的归因建议
    mock_suggestions = [
        AttributionSuggestion(
            lead_id=f"lead_{secrets.token_hex(4)}",
            lead_name="张三",
            lead_phone="138****8000",
            suggested_platform="juliang",
            suggested_ad_account_id="mock_jl_account_1",
            suggested_campaign_name="暑期班抖音推广",
            confidence=0.85,
            match_rule="手机号匹配",
        ),
        AttributionSuggestion(
            lead_id=f"lead_{secrets.token_hex(4)}",
            lead_name="李四",
            lead_phone="139****9000",
            suggested_platform="baidu",
            suggested_ad_account_id="mock_bd_account_1",
            suggested_campaign_name="百度SEM品牌词",
            confidence=0.72,
            match_rule="来源关键词匹配",
        ),
        AttributionSuggestion(
            lead_id=f"lead_{secrets.token_hex(4)}",
            lead_name="王五",
            lead_phone="137****7000",
            suggested_platform="unmatched",
            suggested_ad_account_id=None,
            suggested_campaign_name=None,
            confidence=0.0,
            match_rule=None,
        ),
    ]

    return AttributionSuggestResponse(
        batch_id=batch_id,
        total_leads=3,
        attributed_count=2,
        unmatched_count=1,
        suggestions=mock_suggestions,
    )


@router.get("/leads", response_model=CRMLeadListResponse)
async def list_crm_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    lead_status: Optional[str] = Query(None, description="线索状态筛选"),
    current_user: dict = Depends(get_current_user),
):
    """线索列表（Mock）"""
    async with get_mock_db() as db:
        query = "SELECT * FROM mock_crm_leads WHERE tenant_id = ?"
        params = [current_user["tenant_id"]]

        if lead_status:
            query += " AND lead_status = ?"
            params.append(lead_status)

        query += " LIMIT ? OFFSET ?"
        params.extend([page_size, (page - 1) * page_size])

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        leads = [dict(r) for r in rows]

        # 总数
        count_cursor = await db.execute(
            "SELECT COUNT(*) FROM mock_crm_leads WHERE tenant_id = ?",
            (current_user["tenant_id"],)
        )
        total = (await count_cursor.fetchone())[0]

        return CRMLeadListResponse(
            items=leads,
            total=total,
            page=page,
            page_size=page_size
        )


@router.patch("/leads/{lead_id}")
async def update_crm_lead(
    lead_id: str,
    body: CRMLeadUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    """更新线索信息"""
    # Mock: 更新线索
    update_fields = []
    params = []

    for field, value in body.model_dump(exclude_unset=True).items():
        if value is not None:
            update_fields.append(f"{field} = ?")
            params.append(value)

    if update_fields:
        params.extend([lead_id, current_user["tenant_id"]])
        async with get_mock_db() as db:
            await db.execute(
                f"""UPDATE mock_crm_leads
                   SET {', '.join(update_fields)}, updated_at = ?
                   WHERE id = ? AND tenant_id = ?""",
                [datetime.now().isoformat()] + params
            )
            await db.commit()

    return {"message": "线索已更新", "lead_id": lead_id}


@router.get("/batches", response_model=CRMImportBatchListResponse)
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
        return CRMImportBatchListResponse(
            items=[dict(r) for r in rows],
            total=len(rows)
        )


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

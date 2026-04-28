# BUG-11~14: 缺少 CRM/Analytics API 端点

## Bug 描述

**严重级别**: 🟠 P1
**来源**: 代码审核 P0-2（接口对齐矩阵）
**文件**: `backend/app/api/v1/crm.py`, `backend/app/api/v1/analytics.py`

前端调用的多个 API 端点在后端路由文件中未实现，导致前端 404 错误。

## 缺失端点清单

### CRM 模块（BUG-11~13）

| 端点 | 方法 | 功能 | 前端调用 |
|------|------|------|---------|
| `/crm/upload/{batch_id}/preview` | POST | 字段映射预览 | crmApi.previewMapping |
| `/crm/upload/{batch_id}/confirm` | POST | 确认字段映射 | crmApi.confirmMapping |
| `/crm/upload/{batch_id}/attribution-suggest` | GET | 归因建议 | crmApi.attributionSuggest |
| `/crm/leads/{id}` | PATCH | 更新线索 | crmApi.updateLead |

### Analytics 模块（BUG-14）

| 端点 | 方法 | 功能 | 前端调用 |
|------|------|------|---------|
| `/analytics/cross-table` | GET | 交叉分析 | analyticsApi.getCrossTable |
| `/analytics/cross-table/export` | GET | 导出CSV | analyticsApi.exportCrossTable |

## 修复方案

### 1. CRM 路由补充

- **`POST /crm/upload/{batch_id}/preview`**: 使用 POST 方法（有副作用：触发字段分析），返回 `FieldMappingResponse`，包含字段映射建议和示例数据
- **`POST /crm/upload/{batch_id}/confirm`**: 接收 `ConfirmMappingRequest`，更新批次状态为 `awaiting_attribution`
- **`GET /crm/upload/{batch_id}/attribution-suggest`**: 返回 `AttributionSuggestResponse`，包含每个线索的归因建议
- **`PATCH /crm/leads/{lead_id}`**: 接收 `CRMLeadUpdateRequest`，更新线索信息

### 2. Analytics 路由补充

- **`GET /analytics/cross-table`**: 支持 `dimension_a` 和 `dimension_b` 参数，返回 `CrossTableResponse`
- **`GET /analytics/cross-table/export`**: 导出交叉分析 CSV，使用 `StreamingResponse`

### 3. 额外改进

- CRM 上传路径从硬编码 `/tmp` 改为 `settings.LOCAL_STORAGE_PATH`
- 移除路由内联 Schema 定义，统一使用 `app.schemas.crm` 和 `app.schemas.analytics`
- Analytics `dashboard/status` 接口增加 `scenario` 字段，与前端类型对齐

## 修复文件清单

| 文件 | 修改内容 |
|------|---------|
| `backend/app/api/v1/crm.py` | 新增 preview/confirm/attribution-suggest/leads/{id} 端点 |
| `backend/app/api/v1/analytics.py` | 新增 cross-table/cross-table/export 端点 |

## 修复状态

✅ 已完成 — 2026-04-28

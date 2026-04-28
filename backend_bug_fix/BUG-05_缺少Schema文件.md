# BUG-05: 缺少 Schema 文件

## Bug 描述

**严重级别**: 🔴 P0
**来源**: 代码审核 P0-5
**文件**: `backend/app/schemas/`

后端 schemas 目录仅有 `ad_account.py` 和 `auth.py`，前端 `types/index.ts` 定义了完整的类型系统，但后端缺少对应的 Schema 文件，导致 API 响应结构无法验证和文档化。

## 影响范围

| 缺失文件 | 影响模块 | 关键 Schema |
|---------|---------|------------|
| `onboarding.py` | 引导向导 | OnboardingStatusResponse, UpdateOnboardingRequest |
| `crm.py` | CRM 导入 | FieldMappingResponse, CRMLeadResponse, AttributionSuggestion |
| `analytics.py` | 数据分析 | DashboardMetrics, DashboardStatusResponse, CrossTableRow |
| `report.py` | 报表 | ReportResponse, InsightCard, GenerateReportRequest |

## 修复方案

### 1. 创建 `onboarding.py`
- `OnboardingStatusResponse`: 引导状态（3 步 + completed）
- `UpdateOnboardingRequest`: 更新引导请求
- `CompleteOnboardingResponse`: 完成引导响应

### 2. 创建 `crm.py`
- **上传**: `UploadResponse`, `UploadProgressResponse`
- **字段映射**: `FieldMappingItem`, `FieldMappingResponse`, `ConfirmMappingRequest`
- **归因建议**: `AttributionSuggestion`, `AttributionSuggestResponse`, `ConfirmAttributionRequest`
- **线索**: `CRMLeadResponse`, `CRMLeadUpdateRequest`, `CRMLeadListResponse`
- **批次**: `CRMImportBatchResponse`, `CRMImportBatchListResponse`

### 3. 创建 `analytics.py`
- `DashboardMetrics`: 核心指标（spend/leads/deals/cpe/roi）
- `DashboardStatusResponse`: 数据就绪状态 + scenario 场景标识
- `TrendDataPoint`/`TrendResponse`: 趋势数据
- `ChannelCompareItem`/`ChannelCompareResponse`: 渠道对比
- `CrossTableRow`/`CrossTableResponse`: 交叉分析

### 4. 创建 `report.py`
- `GenerateReportRequest`/`GenerateReportResponse`: 报表生成
- `InsightCard`: 行动建议卡片
- `ReportResponse`/`ReportListResponse`: 报表列表
- `ReportInsightsResponse`: 行动建议
- `ReportDownloadResponse`: 报表下载

## 修复文件清单

| 文件 | 操作 |
|------|------|
| `backend/app/schemas/onboarding.py` | 新增 |
| `backend/app/schemas/crm.py` | 新增 |
| `backend/app/schemas/analytics.py` | 新增 |
| `backend/app/schemas/report.py` | 新增 |

## 验证方式

1. 确认所有 Schema 继承自 `BaseModel`
2. 确认 `response_model` 引用正确
3. 确认 `from_attributes = True` 配置（ORM 映射需要的 Schema）
4. 与前端 `types/index.ts` 类型定义对齐

## 修复状态

✅ 已完成 — 2026-04-28

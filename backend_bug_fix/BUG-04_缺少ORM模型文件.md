# BUG-04: 缺少 ORM 模型文件

## Bug 描述

**严重级别**: 🔴 P0
**来源**: 代码审核 P0-4
**文件**: `backend/app/models/`

后端缺少 `onboarding_status`、`crm_lead`、`crm_import_batch`、`attribution_rule`、`report` 等关键 ORM 模型文件。数据库缺少表结构，Alembic 迁移不完整，对应功能模块全部 500。

## 影响范围

| 缺失文件 | 对应数据库表 | 影响 |
|---------|------------|------|
| `onboarding_status.py` | `onboarding_status` | 引导向导无法持久化 |
| `crm_lead.py` | `crm_leads` | CRM 线索无法存储 |
| `crm_import_batch.py` | `crm_import_batches` | 导入批次无法记录 |
| `attribution_rule.py` | `attribution_rules` | 归因规则无法配置 |
| `report.py` | `reports` | 报表无法生成与存储 |

## 修复方案

### 1. 创建 `onboarding_status.py`

- 一对一关联租户（tenant_id + unique 约束）
- 记录 3 步引导状态：step1_done/step2_done/step3_done
- step1 包含 org_name 和 industry 子字段
- 包含 completed 总状态和 completed_at 时间戳

### 2. 创建 `crm_lead.py`

- 关联租户和导入批次（batch_id）
- 存储线索基本信息：name、phone、email
- 保留原始数据 raw_data（JSON Text）
- 归因信息：attribution_status、attributed_ad_account_id、attribution_confidence 等
- 线索状态：lead_status（new/contacted/qualified/converted/lost）
- 成交信息：deal_amount、deal_date

### 3. 创建 `crm_import_batch.py`

- 使用 Enum 定义批次状态：uploading → processing → awaiting_mapping → awaiting_attribution → importing → completed/failed
- 文件信息：filename、file_path、file_size
- 数据统计：total_rows、processed_rows、success_rows、failed_rows
- 字段映射配置：field_mapping（JSON Text）

### 4. 创建 `attribution_rule.py`

- 使用 Enum 定义匹配模式：exact/contains/regex/fuzzy
- 规则基本信息：name、description
- 匹配条件：match_field、match_mode、keywords（JSON）
- 目标广告账户关联：target_ad_account_id
- 优先级和启用状态：priority、is_active

### 5. 创建 `report.py`

- 使用 Enum 定义报表类型：weekly/monthly/campaign/channel/custom
- 使用 Enum 定义报表状态：generating/ready/failed
- 时间范围：date_range_start、date_range_end
- 报表内容：summary、insights（JSON Text）、data_snapshot
- 文件存储：file_path

## 修复文件清单

| 文件 | 操作 |
|------|------|
| `backend/app/models/onboarding_status.py` | 新增 |
| `backend/app/models/crm_lead.py` | 新增 |
| `backend/app/models/crm_import_batch.py` | 新增 |
| `backend/app/models/attribution_rule.py` | 新增 |
| `backend/app/models/report.py` | 新增 |

## 验证方式

1. 确认所有模型继承自 `Base`，可被 `Base.metadata.create_all` 自动建表
2. 确认外键关联正确（tenant_id → tenants.id 等）
3. 确认 Enum 类型定义完整
4. 运行 `alembic revision --autogenerate` 生成迁移脚本

## 修复状态

✅ 已完成 — 2026-04-28

# BUG-17: models/__init__.py 未导出所有模型

## Bug 描述

**严重级别**: 🔵 P3
**来源**: 代码审核衍生问题
**文件**: `backend/app/models/__init__.py`

模型文件 `__init__.py` 仍为空（仅含注释），导致：
1. Alembic 迁移 `autogenerate` 无法自动发现新增模型
2. `Base.metadata.create_all` 在未显式导入模型时不会创建对应表
3. 其他模块需要逐一 import 模型文件，不够便捷

## 修复方案

在 `__init__.py` 中导入所有模型类，使 Alembic 和 ORM 自动发现：

```python
from app.models.tenant import Tenant
from app.models.user import User
from app.models.ad_account import AdAccount, AdPlatform, AdAccountStatus
from app.models.ad_daily_stat import AdDailyStat
from app.models.onboarding_status import OnboardingStatus
from app.models.crm_lead import CRMLead
from app.models.crm_import_batch import CRMImportBatch, ImportBatchStatus
from app.models.attribution_rule import AttributionRule, RuleMatchMode
from app.models.report import Report, ReportType, ReportStatus
```

## 修复文件清单

| 文件 | 修改内容 |
|------|---------|
| `backend/app/models/__init__.py` | 导入所有模型类和枚举 |

## 修复状态

✅ 已完成 — 2026-04-28

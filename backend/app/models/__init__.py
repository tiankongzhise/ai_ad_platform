"""
数据库模型

所有 ORM 模型必须在此导入，以便 Alembic 迁移自动发现和 Base.metadata.create_all 正确建表。
"""
from app.models.tenant import Tenant
from app.models.user import User
from app.models.ad_account import AdAccount, AdPlatform, AdAccountStatus
from app.models.ad_daily_stat import AdDailyStat
from app.models.onboarding_status import OnboardingStatus
from app.models.crm_lead import CRMLead
from app.models.crm_import_batch import CRMImportBatch, ImportBatchStatus
from app.models.attribution_rule import AttributionRule, RuleMatchMode
from app.models.report import Report, ReportType, ReportStatus

__all__ = [
    "Tenant",
    "User",
    "AdAccount",
    "AdPlatform",
    "AdAccountStatus",
    "AdDailyStat",
    "OnboardingStatus",
    "CRMLead",
    "CRMImportBatch",
    "ImportBatchStatus",
    "AttributionRule",
    "RuleMatchMode",
    "Report",
    "ReportType",
    "ReportStatus",
]

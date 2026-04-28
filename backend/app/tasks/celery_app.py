"""
Celery 应用初始化
"""
from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "eduadcrm",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.sync_ad_tasks",
        "app.tasks.import_tasks",
        "app.tasks.report_tasks",
    ],
)

# Celery 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 任务最大执行时间 1 小时
    task_soft_time_limit=3000,  # 软限制 50 分钟
    worker_prefetch_multiplier=1,  # 防止任务积压
    worker_max_tasks_per_child=100,  # 每个 worker 处理 100 个任务后重启
    # 定时任务配置
    beat_schedule={
        "daily-sync-juliang": {
            "task": "app.tasks.sync_ad_tasks.daily_sync_juliang",
            "schedule": 7200.0,  # 每 2 小时（测试用）
            # 生产环境: crontab(hour=2, minute=0) 每天凌晨 2 点
        },
        "daily-sync-baidu": {
            "task": "app.tasks.sync_ad_tasks.daily_sync_baidu",
            "schedule": 7500.0,  # 每 2.5 小时
            # 生产环境: crontab(hour=2, minute=30) 每天凌晨 2:30
        },
    },
)


# 信号：任务成功后清理
@celery_app.task(ignore_result=True)
def cleanup_old_results():
    """清理旧的任务结果（每天执行）"""
    pass  # TODO: 实现结果清理逻辑
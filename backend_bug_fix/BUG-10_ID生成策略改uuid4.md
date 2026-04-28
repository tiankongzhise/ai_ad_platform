# BUG-10: ID 生成策略使用时间戳，高并发可能重复

## Bug 描述

**严重级别**: 🟡 P2
**来源**: 代码审核 P2-5
**文件**: 多个模型文件

`AdAccount`、`AdDailyStat`、`User`、`Tenant` 四个模型均使用 `datetime.now().strftime('%Y%m%d%H%M%S%f')` 生成 ID。虽然微秒精度理论上足够，但：
1. 并发创建时操作系统时间分辨率不保证微秒唯一
2. 风格不一致（UUID 规范是 36 字符含连字符）
3. 生成的 ID 带有业务前缀（ada_/ads_/usr_/ten_），暴露内部结构

## 修复方案

统一使用 `uuid.uuid4()` 生成 ID：

```python
# 修复前
id: Mapped[str] = mapped_column(
    String(36), primary_key=True,
    default=lambda: f"ada_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
)

# 修复后
import uuid
id: Mapped[str] = mapped_column(
    String(36), primary_key=True,
    default=lambda: str(uuid.uuid4())
)
```

## 修复文件清单

| 文件 | 修改内容 |
|------|---------|
| `backend/app/models/ad_account.py` | ID 生成改为 uuid4 |
| `backend/app/models/ad_daily_stat.py` | ID 生成改为 uuid4 |
| `backend/app/models/user.py` | ID 生成改为 uuid4 |
| `backend/app/models/tenant.py` | ID 生成改为 uuid4 |

## 修复状态

✅ 已完成 — 2026-04-28

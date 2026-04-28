# BUG-16: datetime.now() 未使用 UTC，Token 过期时间存在时区风险

## Bug 描述

**严重级别**: 🔵 P3
**来源**: 代码审核 P3-3
**文件**: `backend/app/api/v1/ad_accounts.py`

OAuth 回调和同步状态中多处使用 `datetime.now()`（本地时间，无时区信息），若服务器时区与数据库时区不一致（常见于容器化部署），Token 过期时间计算会偏差。

## 影响位置

- 巨量引擎回调：token_expires_at 计算（2处）
- 百度营销回调：token_expires_at 计算（2处）
- 同步状态：started_at 字段（3处）
- 手动同步：estimated_completion 计算（1处）

## 修复方案

统一使用 `datetime.now(timezone.utc)` 替代 `datetime.now()`：

```python
# 修复前
token_expires_at = datetime.now() + timedelta(seconds=token_info.expires_in)
started_at = datetime.now().isoformat()

# 修复后
from datetime import datetime, timedelta, timezone
token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_info.expires_in)
started_at = datetime.now(timezone.utc).isoformat()
```

## 修复文件清单

| 文件 | 修改内容 |
|------|---------|
| `backend/app/api/v1/ad_accounts.py` | 所有 datetime.now() 改为 datetime.now(timezone.utc) |

## 修复状态

✅ 已完成 — 2026-04-28

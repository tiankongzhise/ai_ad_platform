# BUG-07: SyncStatusResponse.last_sync_at 类型不一致

## Bug 描述

**严重级别**: 🟡 P2
**来源**: 代码审核 P2-3
**文件**: `backend/app/schemas/ad_account.py`

后端 Schema 定义 `last_sync_at: Optional[datetime]`，但 Redis 存储的 `finished_at` 是手动 `.isoformat()` 的字符串。当从 Redis 读取后经 Pydantic 反序列化时，字符串→datetime 转换依赖格式，可能失败。

## 修复方案

将 `last_sync_at` 类型改为 `Optional[str]`，显式使用 ISO 格式字符串，与 Redis 数据保持一致，避免 datetime 反序列化问题。

```python
# 修复前
last_sync_at: Optional[datetime] = None

# 修复后
last_sync_at: Optional[str] = None  # ISO 格式字符串，与 Redis 存储一致
```

## 修复文件清单

| 文件 | 修改内容 |
|------|---------|
| `backend/app/schemas/ad_account.py` | last_sync_at 类型从 datetime 改为 str |

## 修复状态

✅ 已完成 — 2026-04-28

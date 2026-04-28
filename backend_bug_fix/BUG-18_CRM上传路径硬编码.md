# BUG-18: CRM 上传文件路径硬编码 /tmp

## Bug 描述

**严重级别**: 🔵 P3
**来源**: 代码审核衍生问题
**文件**: `backend/app/api/v1/crm.py`

CRM 上传路由中文件保存路径硬编码为 `/tmp/crm_uploads`，Windows 环境下 `/tmp` 不存在，导致上传功能在 Windows 上完全失败。应使用 `settings.LOCAL_STORAGE_PATH` 配置项。

## 修复方案

```python
# 修复前
temp_dir = "/tmp/crm_uploads"
os.makedirs(temp_dir, exist_ok=True)

# 修复后
upload_dir = os.path.join(settings.LOCAL_STORAGE_PATH, "crm_uploads")
os.makedirs(upload_dir, exist_ok=True)
```

## 修复文件清单

| 文件 | 修改内容 |
|------|---------|
| `backend/app/api/v1/crm.py` | 上传路径改为 settings.LOCAL_STORAGE_PATH |

## 注意

此修复已在 BUG-11~14 的 CRM 路由重写中一并完成。

## 修复状态

✅ 已完成 — 2026-04-28

# BUG-08: OAuthCallbackResponse Schema 死代码

## Bug 描述

**严重级别**: 🟡 P2
**来源**: 代码审核 P2-4
**文件**: `backend/app/schemas/ad_account.py`, `backend/app/api/v1/ad_accounts.py`

`OAuthCallbackResponse` Schema 定义存在但实际回调接口从不返回该格式——OAuth 回调始终返回 `RedirectResponse(302)`，永远不会返回 JSON。该 Schema 成为死代码，且误导前端开发者以为可以手动调用回调接口获取 JSON 响应。

## 修复方案

1. 删除 `OAuthCallbackResponse` Schema 类
2. 删除路由文件中对 `OAuthCallbackResponse` 的 import

```python
# 删除的 Schema
class OAuthCallbackResponse(BaseModel):
    """OAuth 回调响应"""
    status: str = "success"
    ad_account_id: str
    account_name: str
    next_step: str = "crm_import"
    message: str = "巨量引擎授权成功"
```

## 修复文件清单

| 文件 | 修改内容 |
|------|---------|
| `backend/app/schemas/ad_account.py` | 删除 OAuthCallbackResponse 类 |
| `backend/app/api/v1/ad_accounts.py` | 删除 OAuthCallbackResponse import |

## 修复状态

✅ 已完成 — 2026-04-28

# BUG-09: OAuth 回调 state 为空时降级为 default_tenant（安全漏洞）

## Bug 描述

**严重级别**: 🟡 P2
**来源**: 代码审核 P2-1
**文件**: `backend/app/api/v1/ad_accounts.py`（第 190-193 行）

巨量引擎 OAuth 回调中，当 `state` 为空时，后端降级为 `default_tenant`。这意味着任何人直接访问 `/api/v1/ad/juliang/callback?code=xxx`（不携带 state），都会以 `default_tenant` 身份创建广告账户。这是多租户系统的越权漏洞。

注意：百度营销的回调已正确实现了 `ALLOW_OAUTH_STATE_DOWNGRADE` 环境变量控制，但巨量引擎回调缺失此安全机制。

## 修复方案

参考百度回调的实现，为巨量引擎回调添加 `settings.DEBUG` 判断：

```python
# 修复前
if not tenant_id:
    logger.warning("OAuth 回调未携带有效 state，使用降级租户 ID（仅开发环境）")
    tenant_id = "default_tenant"

# 修复后
if not tenant_id:
    if settings.DEBUG:
        logger.warning("OAuth 回调未携带有效 state，降级到默认租户（仅开发环境）")
        tenant_id = "default_tenant"
    else:
        logger.warning("生产环境拒绝无 state 的 OAuth 回调")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/ad-accounts?oauth_result=error&platform=juliang&reason=missing_state",
            status_code=302,
        )
```

## 修复文件清单

| 文件 | 修改内容 |
|------|---------|
| `backend/app/api/v1/ad_accounts.py` | 巨量引擎回调 state 为空时增加 DEBUG 判断 |

## 修复状态

✅ 已完成 — 2026-04-28

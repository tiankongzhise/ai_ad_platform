# BUG-03: TenantContext 上下文泄漏

## Bug 描述

**严重级别**: 🔴 P0（已部分修复，补充修复）
**来源**: 代码审核 P0-3（衍生问题）
**文件**: `backend/app/core/tenant.py`

审核指出 TenantContext 使用类变量存在并发安全问题，实际代码已使用 ContextVar 修复。但进一步分析发现：`TenantContext.clear()` 方法在请求结束后从未被调用。虽然在标准 asyncio 中每个请求是独立协程，ContextVar 会随协程销毁而清理，但在某些 ASGI 服务器中协程可能被复用，导致上下文残留。

## 修复方案

添加 `TenantContextCleanupMiddleware` 中间件，在请求结束后自动调用 `TenantContext.clear()`：

```python
class TenantContextCleanupMiddleware(BaseHTTPMiddleware):
    """请求结束后自动清理 TenantContext"""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        finally:
            TenantContext.clear()
```

在 `main.py` 中注册该中间件。

## 修复文件清单

| 文件 | 修改内容 |
|------|---------|
| `backend/app/core/tenant.py` | 添加 TenantContextCleanupMiddleware 类 |
| `backend/app/main.py` | 注册 TenantContextCleanupMiddleware |

## 修复状态

✅ 已完成 — 2026-04-28

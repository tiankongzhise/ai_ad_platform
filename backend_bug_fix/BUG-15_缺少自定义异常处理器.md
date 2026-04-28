# BUG-15: 缺少 EduAdCRMException 专用异常处理器

## Bug 描述

**严重级别**: 🔵 P3
**来源**: 代码审核 P3-2
**文件**: `backend/app/main.py`

main.py 只注册了 `HTTPException` 和通用 `Exception` 两个异常处理器，但自定义的 `EduAdCRMException`（继承自 HTTPException）不会被正确格式化。EduAdCRMException 包含 `code` 和 `extra` 字段，这些信息在走 HTTPException handler 时会丢失。

## 修复方案

在 main.py 中添加 `EduAdCRMException` 专用异常处理器：

```python
from app.core.exceptions import EduAdCRMException

@app.exception_handler(EduAdCRMException)
async def edu_exception_handler(request: Request, exc: EduAdCRMException):
    """业务自定义异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.detail,
            "extra": exc.extra,
        },
    )
```

注意：EduAdCRMException 继承自 HTTPException，因此此 handler 必须注册在 HTTPException handler 之前（FastAPI 按子类优先匹配）。

## 修复文件清单

| 文件 | 修改内容 |
|------|---------|
| `backend/app/main.py` | 添加 EduAdCRMException 异常处理器 |

## 修复状态

✅ 已完成 — 2026-04-28

"""
FastAPI 应用入口
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.ad_accounts import router as ad_accounts_router
from app.api.v1.auth import router as auth_router
from app.api.v1.demo import router as demo_router
from app.api.v1.onboarding import router as onboarding_router
from app.api.v1.crm import router as crm_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.reports import router as reports_router
from app.api.v1.settings import router as settings_router
from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.redis_client import close_redis, get_redis
from app.core.tenant import TenantContextCleanupMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时：初始化数据库 + 预热 Redis 连接
    await init_db()
    await get_redis()        # 预热连接池，启动即可用
    
    # 初始化 Mock 数据库（如果启用）
    from app.mock.mock_db import init_mock_db, is_mock_mode
    if is_mock_mode():
        try:
            await init_mock_db()
            import logging
            logger = logging.getLogger(__name__)
            logger.info("Mock 数据库初始化完成")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Mock 数据库初始化失败: {e}")
    
    yield
    # 关闭时：释放所有连接
    await close_db()
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ==================== 中间件 ====================

# 租户上下文清理中间件（必须在 CORS 之前注册）
app.add_middleware(TenantContextCleanupMiddleware)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 全局异常处理 ====================

from fastapi import HTTPException

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


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """FastAPI HTTP 异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": "HTTP_ERROR",
            "message": exc.detail,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": "INTERNAL_ERROR",
            "message": "服务器内部错误",
            "detail": str(exc) if settings.DEBUG else None,
        },
    )


# ==================== 健康检查 ====================

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


# ==================== 注册路由 ====================

# 认证路由
app.include_router(
    auth_router,
    prefix=settings.API_V1_PREFIX,
)

# 广告账户路由（包含巨量引擎/百度 OAuth）
app.include_router(
    ad_accounts_router,
    prefix=settings.API_V1_PREFIX,
)

# 演示数据路由 (Mock)
app.include_router(
    demo_router,
    prefix=settings.API_V1_PREFIX,
)

# 引导向导路由 (Mock)
app.include_router(
    onboarding_router,
    prefix=settings.API_V1_PREFIX,
)

# CRM 路由 (混合)
app.include_router(
    crm_router,
    prefix=settings.API_V1_PREFIX,
)

# 数据分析路由 (Mock)
app.include_router(
    analytics_router,
    prefix=settings.API_V1_PREFIX,
)

# 报表路由 (Mock)
app.include_router(
    reports_router,
    prefix=settings.API_V1_PREFIX,
)

# 设置路由 (混合)
app.include_router(
    settings_router,
    prefix=settings.API_V1_PREFIX,
)
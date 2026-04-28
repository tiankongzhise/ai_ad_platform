"""
FastAPI 应用入口
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.ad_accounts import router as ad_accounts_router
from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.redis_client import close_redis, get_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时：初始化数据库 + 预热 Redis 连接
    await init_db()
    await get_redis()        # 预热连接池，启动即可用
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

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 全局异常处理 ====================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
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

# 广告账户路由（包含巨量引擎/百度 OAuth）
app.include_router(
    ad_accounts_router,
    prefix=settings.API_V1_PREFIX,
)
# EduAdCRM 第一阶段敏捷开发技术文档

> **文档版本**：v1.0  
> **制定日期**：2026-04-28  
> **计划周期**：5 个工作日（1 周冲刺）  
> **目标**：前后端联调全部打通，核心三大功能可演示，Mock 层保底兜底

---

## 一、技术架构总览

### 1.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              前端 (React + TypeScript)                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │  登录/注册   │ │  广告账户    │ │  仪表盘      │ │  CRM导入    │           │
│  │  /login     │ │ /ad-accounts│ │ /dashboard  │ │  /crm       │           │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼ HTTP/REST API
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FastAPI 后端服务                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        API 路由层 (8个模块)                          │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │   │
│  │  │  auth   │ │   ad    │ │  demo   │ │   crm   │ │ analytics│       │   │
│  │  │ [REAL]  │ │ [REAL]  │ │ [MOCK]  │ │ [MIXED] │ │ [MOCK]   │       │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘       │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐                               │   │
│  │  │onboarding│ │ reports │ │settings │                               │   │
│  │  │ [MIXED] │ │ [MOCK]  │ │ [MIXED] │                               │   │
│  │  └─────────┘ └─────────┘ └─────────┘                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        数据层                                        │   │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │   │
│  │  │   MySQL (真实)   │    │  SQLite (Mock)  │    │  Redis (缓存)    │  │   │
│  │  │  - users        │    │  - mock_crm_leads│   │  - oauth_state  │  │   │
│  │  │  - tenants      │    │  - mock_reports  │   │  - sync_status  │  │   │
│  │  │  - ad_accounts  │    │  - mock_dashboard│   │  - jwt_blacklist│  │   │
│  │  │  - ad_daily_stat│    │  - mock_onboarding│  │                 │  │   │
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 技术栈版本

| 层级 | 技术 | 版本 |
|------|------|------|
| 后端框架 | FastAPI | ^0.104.0 |
| ORM | SQLAlchemy | ^2.0.0 |
| 异步驱动 | aiomysql / aiosqlite | ^0.2.0 |
| 缓存 | Redis (aioredis) | ^5.0.0 |
| 认证 | python-jose + passlib | ^3.3.0 |
| 任务队列 | Celery | ^5.3.0 |
| 数据库 | MySQL 8.0 + SQLite 3 |

---

## 二、核心模块技术设计

### 2.1 认证模块 (auth.py) - [REAL]

#### 2.1.1 接口清单

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| POST | /auth/register | 用户注册 + 自动创建租户 | 公开 |
| POST | /auth/login | 用户登录，签发 JWT | 公开 |
| POST | /auth/logout | 登出，Token 加入黑名单 | Bearer |
| POST | /auth/refresh | 刷新 Access Token | Bearer |
| GET | /auth/profile | 获取当前用户信息 | Bearer |

#### 2.1.2 JWT Token 规范

```python
# Access Token Payload
{
    "sub": "usr_20250428120000000000",      # user_id
    "tenant_id": "ten_20250428120000000000", # tenant_id
    "type": "access",
    "exp": 1714291200,                       # 2小时后过期
    "iat": 1714284000,
    "jti": "uuid-for-blacklist"              # 用于登出黑名单
}

# Refresh Token Payload
{
    "sub": "usr_20250428120000000000",
    "tenant_id": "ten_20250428120000000000",
    "type": "refresh",
    "exp": 1714888800,                       # 7天后过期
    "iat": 1714284000
}
```

#### 2.1.3 注册流程时序

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│  Client │     │  auth   │     │  User   │     │ Tenant  │
└────┬────┘     └────┬────┘     └────┬────┘     └────┬────┘
     │               │               │               │
     │ POST /register│               │               │
     │──────────────>│               │               │
     │               │               │               │
     │               │ BEGIN TX      │               │
     │               │──────────────>│               │
     │               │               │               │
     │               │ INSERT tenant │               │
     │               │──────────────────────────────>│
     │               │               │               │
     │               │ INSERT user   │               │
     │               │──────────────>│               │
     │               │               │               │
     │               │ COMMIT        │               │
     │               │──────────────>│               │
     │               │               │               │
     │  201 Created  │               │               │
     │  + JWT Tokens │               │               │
     │<──────────────│               │               │
```

### 2.2 Mock 数据层设计

#### 2.2.1 SQLite Mock 数据库结构

```sql
-- Mock 数据库文件: backend/mock_data.sqlite3

-- 演示仪表盘趋势数据（30天）
CREATE TABLE mock_dashboard_trend (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    date TEXT NOT NULL,           -- YYYY-MM-DD
    spend REAL DEFAULT 0,         -- 广告花费
    leads INTEGER DEFAULT 0,      -- 线索数
    deals INTEGER DEFAULT 0,      -- 成交数
    deal_amount REAL DEFAULT 0,   -- 成交金额
    platform TEXT,                -- 'juliang' | 'baidu' | 'combined'
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_trend_tenant_date ON mock_dashboard_trend(tenant_id, date);

-- 演示线索数据
CREATE TABLE mock_crm_leads (
    id TEXT PRIMARY KEY,          -- lead_xxx
    tenant_id TEXT NOT NULL,
    batch_id TEXT,                -- 导入批次
    name TEXT,
    phone_masked TEXT,            -- 138****8888
    phone_hash TEXT,              -- SHA256 用于去重
    source_channel TEXT,          -- '抖音' | '百度' | '微信' | '其他'
    course_name TEXT,
    deal_status TEXT DEFAULT 'following', -- 'deal' | 'no_deal' | 'following'
    deal_amount REAL DEFAULT 0,
    attribution_rule_id TEXT,
    created_at TEXT,
    updated_at TEXT
);
CREATE INDEX idx_leads_tenant ON mock_crm_leads(tenant_id);
CREATE INDEX idx_leads_batch ON mock_crm_leads(batch_id);

-- 导入批次记录
CREATE TABLE mock_crm_batches (
    id TEXT PRIMARY KEY,          -- batch_xxx
    tenant_id TEXT NOT NULL,
    filename TEXT,
    total_rows INTEGER DEFAULT 0,
    processed_rows INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending', -- 'pending' | 'processing' | 'completed' | 'failed'
    mapping_confirmed INTEGER DEFAULT 0,
    attribution_confirmed INTEGER DEFAULT 0,
    created_at TEXT,
    completed_at TEXT
);

-- 演示报表
CREATE TABLE mock_reports (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    report_type TEXT,             -- 'daily' | 'weekly' | 'monthly'
    date_range_start TEXT,
    date_range_end TEXT,
    status TEXT DEFAULT 'ready',  -- 'generating' | 'ready' | 'failed'
    file_path TEXT,               -- 模拟文件路径
    insights TEXT,                -- JSON 行动建议
    created_at TEXT
);

-- 引导状态
CREATE TABLE mock_onboarding (
    tenant_id TEXT PRIMARY KEY,
    step1_done INTEGER DEFAULT 0,
    step1_org_name TEXT,
    step1_industry TEXT,
    step2_done INTEGER DEFAULT 0,  -- 广告账户绑定
    step3_done INTEGER DEFAULT 0,  -- CRM 导入
    completed_at TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 归因规则
CREATE TABLE mock_attribution_rules (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    name TEXT,
    platform TEXT,
    keywords TEXT,                -- JSON ["关键词1", "关键词2"]
    priority INTEGER DEFAULT 0,
    created_at TEXT
);
```

#### 2.2.2 Mock 数据生成策略

```python
# backend/app/mock/seed.py

DEMO_CONFIG = {
    "org_name": "星海教育",
    "industry": "K12教育",
    "daily_spend_range": (8000, 15000),    # 元
    "cpe_range": (30, 50),                  # 元/线索
    "roi_range": (3.0, 6.0),
    "juliang_spend_ratio": 0.6,             # 抖音占 60% 预算
    "baidu_spend_ratio": 0.4,
    "total_leads_30d": 1200,
    "deal_rate": 0.18,                      # 成交率 18%
    "courses": ["小学数学", "初中英语", "高中物理", "少儿编程"],
    "channels": ["抖音", "百度", "微信朋友圈", "知乎"],
}

def generate_30d_trend(tenant_id: str) -> list[dict]:
    """生成30天演示趋势数据"""
    data = []
    base_date = datetime.now() - timedelta(days=30)
    
    for i in range(30):
        date = base_date + timedelta(days=i)
        
        # 抖音数据 (60%)
        jl_spend = random.uniform(4800, 9000)
        jl_leads = int(jl_spend / random.uniform(30, 50))
        
        # 百度数据 (40%)
        bd_spend = random.uniform(3200, 6000)
        bd_leads = int(bd_spend / random.uniform(35, 55))
        
        data.append({
            "tenant_id": tenant_id,
            "date": date.strftime("%Y-%m-%d"),
            "spend": round(jl_spend + bd_spend, 2),
            "leads": jl_leads + bd_leads,
            "deals": int((jl_leads + bd_leads) * 0.18),
            "deal_amount": round((jl_leads + bd_leads) * 0.18 * 5000, 2),
            "platform": "combined"
        })
    
    return data
```

### 2.3 广告账户模块 (ad_accounts.py) - [REAL]

#### 2.3.1 OAuth 流程状态机

```
                    ┌─────────────┐
                    │   初始状态   │
                    └──────┬──────┘
                           │ 点击绑定
                           ▼
                    ┌─────────────┐
                    │ state生成   │◄──── Redis: oauth_state:{state}
                    │ 跳转授权页  │      TTL=10min
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │  用户授权    │ │  用户拒绝    │ │  state过期   │
    │   成功      │ │             │ │             │
    └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
           │               │               │
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │ code换token │ │ 重定向到前端 │ │ 重定向到前端 │
    │ 创建账户    │ │ ?cancelled  │ │ ?error      │
    │ 触发同步    │ │             │ │             │
    └──────┬──────┘ └─────────────┘ └─────────────┘
           │
           ▼
    ┌─────────────┐
    │ 重定向到前端 │
    │ ?success    │
    └─────────────┘
```

#### 2.3.2 百度 OAuth 回调实现

```python
# backend/app/api/v1/ad_accounts.py (已存在，需要补全)

@router.get("/baidu/callback", summary="百度营销 OAuth 回调")
async def baidu_oauth_callback(
    code: str = Query(...),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """百度营销 OAuth 回调处理 - 已完整实现"""
    # 实现已在代码中，无需修改
```

### 2.4 CRM 模块 (crm.py) - [MIXED]

#### 2.4.1 混合实现策略

| 功能 | 实现方式 | 说明 |
|------|----------|------|
| 文件上传 | REAL | 真实接收文件，保存到临时目录 |
| 异步处理 | REAL | Celery 任务处理 Excel |
| 进度查询 | REAL | Redis 存储真实进度 |
| 字段预览 | MOCK | SQLite 返回模拟字段分析 |
| 字段确认 | MOCK | 写入 SQLite |
| 归因建议 | MOCK | 返回模拟建议 |
| 线索列表 | MOCK | 从 SQLite 读取 |

#### 2.4.2 文件上传流程

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Client │    │  crm    │    │  Temp   │    │  Celery │    │  Redis  │
└────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘
     │              │              │              │              │
     │ POST /upload │              │              │              │
     │ + Excel文件  │              │              │              │
     │─────────────>│              │              │              │
     │              │              │              │              │
     │              │ 保存临时文件  │              │              │
     │              │─────────────>│              │              │
     │              │              │              │              │
     │              │ 触发 Celery  │              │              │
     │              │────────────────────────────>│              │
     │              │              │              │              │
     │ 返回 batch_id│              │              │              │
     │ + task_id    │              │              │              │
     │<─────────────│              │              │              │
     │              │              │              │              │
     │ GET /upload/{task_id}       │              │              │
     │────────────────────────────>│              │              │
     │              │              │              │ 查询进度      │
     │              │              │              │─────────────>│
     │              │              │              │              │
     │ 返回进度     │              │              │              │
     │<────────────────────────────│              │              │
```

### 2.5 仪表盘分析模块 (analytics.py) - [MOCK]

#### 2.5.1 接口清单

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /analytics/dashboard | 仪表盘核心指标 |
| GET | /analytics/dashboard/status | 数据就绪状态检查 |
| GET | /analytics/trend | 30天趋势数据 |
| GET | /analytics/channel-compare | 渠道对比分析 |
| GET | /analytics/cross-table | 交叉分析表格 |
| GET | /analytics/cross-table/export | 导出 CSV |

#### 2.5.2 核心指标计算

```python
# 从 SQLite Mock 数据聚合计算

async def get_dashboard_metrics(tenant_id: str) -> dict:
    """获取仪表盘核心指标"""
    async with get_mock_db() as db:
        # 总花费
        spend_result = await db.execute(
            "SELECT SUM(spend) FROM mock_dashboard_trend WHERE tenant_id = ?",
            (tenant_id,)
        )
        total_spend = spend_result.scalar() or 0
        
        # 总线索
        leads_result = await db.execute(
            "SELECT SUM(leads) FROM mock_dashboard_trend WHERE tenant_id = ?",
            (tenant_id,)
        )
        total_leads = leads_result.scalar() or 0
        
        # 总成交
        deals_result = await db.execute(
            "SELECT SUM(deals) FROM mock_dashboard_trend WHERE tenant_id = ?",
            (tenant_id,)
        )
        total_deals = deals_result.scalar() or 0
        
        # 成交金额
        amount_result = await db.execute(
            "SELECT SUM(deal_amount) FROM mock_dashboard_trend WHERE tenant_id = ?",
            (tenant_id,)
        )
        total_amount = amount_result.scalar() or 0
        
        return {
            "total_spend": round(total_spend, 2),
            "total_leads": total_leads,
            "total_deals": total_deals,
            "total_deal_amount": round(total_amount, 2),
            "cpe": round(total_spend / total_leads, 2) if total_leads > 0 else 0,
            "roi": round(total_amount / total_spend, 2) if total_spend > 0 else 0,
            "deal_rate": round(total_deals / total_leads * 100, 2) if total_leads > 0 else 0,
        }
```

---

## 三、关键代码实现

### 3.1 ContextVar 并发安全修复

```python
# backend/app/core/tenant.py

from contextvars import ContextVar

# 使用 ContextVar 替代类变量，确保并发安全
_tenant_id_var: ContextVar[str] = ContextVar('tenant_id', default=None)
_user_id_var: ContextVar[str] = ContextVar('user_id', default=None)

class TenantContext:
    """租户上下文（基于 ContextVar，线程/协程安全）"""
    
    @classmethod
    def set(cls, tenant_id: str, user_id: str) -> None:
        _tenant_id_var.set(tenant_id)
        _user_id_var.set(user_id)
    
    @classmethod
    def get_tenant_id(cls) -> Optional[str]:
        return _tenant_id_var.get()
    
    @classmethod
    def get_user_id(cls) -> Optional[str]:
        return _user_id_var.get()
    
    @classmethod
    def clear(cls) -> None:
        _tenant_id_var.set(None)
        _user_id_var.set(None)
```

### 3.2 SQLite Mock 连接管理

```python
# backend/app/mock/mock_db.py

import aiosqlite
from contextlib import asynccontextmanager
from pathlib import Path

MOCK_DB_PATH = Path(__file__).parent.parent.parent / "mock_data.sqlite3"

@asynccontextmanager
async def get_mock_db():
    """获取 SQLite Mock 数据库连接"""
    async with aiosqlite.connect(MOCK_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db

async def init_mock_db():
    """初始化 Mock 数据库表结构"""
    async with get_mock_db() as db:
        # 执行 schema.sql 创建表
        schema_path = Path(__file__).parent / "schema.sql"
        if schema_path.exists():
            with open(schema_path) as f:
                await db.executescript(f.read())
            await db.commit()
```

### 3.3 认证路由核心实现

```python
# backend/app/api/v1/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis_client import add_token_to_blacklist
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_access_token,
    verify_password,
    verify_refresh_token,
)
from app.core.tenant import get_current_user
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["认证"])

@router.post("/register", response_model=LoginResponse, status_code=201)
async def register(
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """用户注册 - 同时创建租户"""
    # 检查邮箱是否已存在
    existing = await db.execute(
        select(User).where(User.email == req.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="邮箱已被注册"
        )
    
    # 创建租户
    tenant = Tenant(name=req.org_name or req.email.split("@")[0])
    db.add(tenant)
    await db.flush()  # 获取 tenant.id
    
    # 创建用户
    user = User(
        tenant_id=tenant.id,
        email=req.email,
        password_hash=get_password_hash(req.password),
        name=req.name,
        role="admin",  # 第一个用户是管理员
    )
    db.add(user)
    await db.commit()
    
    # 签发 Token
    access_token = create_access_token(
        data={"sub": user.id, "tenant_id": tenant.id}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.id, "tenant_id": tenant.id}
    )
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )

@router.post("/login", response_model=LoginResponse)
async def login(
    req: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """用户登录"""
    result = await db.execute(
        select(User).where(User.email == req.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误"
        )
    
    # 更新最后登录时间
    user.last_login_at = datetime.now()
    await db.commit()
    
    access_token = create_access_token(
        data={"sub": user.id, "tenant_id": user.tenant_id}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.id, "tenant_id": user.tenant_id}
    )
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )

@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user),
):
    """用户登出 - Token 加入黑名单"""
    # TODO: 从请求头获取 jti，加入 Redis 黑名单
    return {"message": "登出成功"}

@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    req: RefreshTokenRequest,
):
    """刷新 Access Token"""
    payload = verify_refresh_token(req.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token 无效或已过期"
        )
    
    new_access_token = create_access_token(
        data={"sub": payload["sub"], "tenant_id": payload["tenant_id"]}
    )
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
    }

@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户信息"""
    result = await db.execute(
        select(User).where(User.id == current_user["user_id"])
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return UserResponse.model_validate(user)
```

### 3.4 认证 Schema

```python
# backend/app/schemas/auth.py

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """注册请求"""
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: Optional[str] = None
    org_name: Optional[str] = None


class LoginRequest(BaseModel):
    """登录请求"""
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """刷新 Token 请求"""
    refresh_token: str


class UserResponse(BaseModel):
    """用户信息响应"""
    id: str
    email: str
    name: Optional[str]
    role: str
    tenant_id: str
    created_at: datetime
    
    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
```

---

## 四、路由注册配置

```python
# backend/app/main.py (修改)

from app.api.v1.ad_accounts import router as ad_accounts_router
from app.api.v1.auth import router as auth_router
from app.api.v1.demo import router as demo_router
from app.api.v1.onboarding import router as onboarding_router
from app.api.v1.crm import router as crm_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.reports import router as reports_router
from app.api.v1.settings import router as settings_router

# ==================== 注册路由 ====================

# 认证路由
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)

# 广告账户路由（包含巨量引擎/百度 OAuth）
app.include_router(ad_accounts_router, prefix=settings.API_V1_PREFIX)

# 演示数据路由
app.include_router(demo_router, prefix=settings.API_V1_PREFIX)

# 引导向导路由
app.include_router(onboarding_router, prefix=settings.API_V1_PREFIX)

# CRM 路由
app.include_router(crm_router, prefix=settings.API_V1_PREFIX)

# 数据分析路由
app.include_router(analytics_router, prefix=settings.API_V1_PREFIX)

# 报表路由
app.include_router(reports_router, prefix=settings.API_V1_PREFIX)

# 设置路由
app.include_router(settings_router, prefix=settings.API_V1_PREFIX)
```

---

## 五、接口实现策略汇总

| 模块 | 接口 | 策略 | 优先级 |
|------|------|------|--------|
| auth | POST /auth/register | REAL | P0 |
| auth | POST /auth/login | REAL | P0 |
| auth | POST /auth/logout | REAL | P0 |
| auth | POST /auth/refresh | REAL | P0 |
| auth | GET /auth/profile | REAL | P0 |
| ad | GET /ad/juliang/oauth-url | REAL (已有) | P0 |
| ad | GET /ad/baidu/oauth-url | REAL (已有) | P0 |
| ad | GET /ad/juliang/callback | REAL (已有) | P0 |
| ad | GET /ad/baidu/callback | REAL (已有) | P0 |
| ad | GET /ad/accounts | REAL (已有) | P0 |
| demo | GET /demo/dashboard | MOCK | P1 |
| demo | GET /demo/metrics | MOCK | P1 |
| onboarding | GET /onboarding/status | MIXED | P1 |
| onboarding | POST /onboarding/status | MIXED | P1 |
| onboarding | POST /onboarding/complete | MIXED | P1 |
| crm | POST /crm/upload | MIXED | P1 |
| crm | GET /crm/upload/{task_id} | REAL | P1 |
| crm | POST /crm/upload/{batch_id}/preview | MOCK | P1 |
| crm | POST /crm/upload/{batch_id}/confirm | MOCK | P1 |
| crm | GET /crm/leads | MOCK | P1 |
| analytics | GET /analytics/dashboard | MOCK | P1 |
| analytics | GET /analytics/dashboard/status | MIXED | P1 |
| analytics | GET /analytics/trend | MOCK | P2 |
| reports | GET /reports | MOCK | P2 |
| settings | GET /settings/tenant | REAL | P2 |
| settings | PATCH /settings/tenant | REAL | P2 |

---

## 六、测试策略

### 6.1 单元测试重点

```python
# 测试文件: backend/tests/test_auth.py

async def test_register_creates_tenant_and_user(client, db):
    """测试注册同时创建租户和用户"""
    response = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
        "org_name": "测试机构"
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["tenant_id"] is not None

async def test_tenant_context_isolation(client, db):
    """测试租户上下文并发隔离"""
    # 并发请求不同租户，验证数据隔离
    pass
```

### 6.2 联调测试清单

| 测试项 | 预期结果 | 验证方式 |
|--------|----------|----------|
| 用户注册 | 201，自动创建租户 | 检查 MySQL |
| 用户登录 | 200，返回双 Token | 响应体检查 |
| Token 刷新 | 200，返回新 access_token | 响应体检查 |
| 登出 | 200，Token 加入黑名单 | Redis 检查 |
| 百度 OAuth 跳转 | 整页跳转 | 浏览器验证 |
| 百度 OAuth 回调 | 302 到前端 success | 网络面板 |
| 演示数据 | 返回"星海教育"数据 | 响应体检查 |
| CRM 上传 | 返回 batch_id + task_id | 响应体检查 |

---

## 七、风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| ContextVar 兼容性问题 | 高 | 提前测试 Python 3.9+ 兼容性 |
| SQLite 并发写入 | 中 | 使用 WAL 模式，单连接池 |
| Mock 数据质量差 | 中 | 精心设计"星海教育"数据集 |
| Celery 任务失败 | 低 | 添加重试机制和错误日志 |
| 前端接口签名不匹配 | 中 | 对照前端 Store 确认字段名 |

---

*技术文档制定：2026-04-28 | 基于 sprint-plan-quickwin.md 细化*

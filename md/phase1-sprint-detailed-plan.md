# EduAdCRM 第一阶段敏捷开发详细安排

> **文档版本**：v1.0  
> **制定日期**：2026-04-28  
> **冲刺周期**：5 个工作日（2026-04-28 至 2026-05-02）  
> **执行团队**：1 名后端开发者 + 1 名前端开发者（或全栈单人）

---

## 一、每日任务分解

### Day 1（2026-04-28）：基础设施修复

#### 🎯 当日目标
- [ ] 修复 TenantContext 并发安全漏洞
- [ ] 创建 SQLite Mock 层基础设施
- [ ] 创建 auth.py 认证路由（真实逻辑）
- [ ] 注册所有路由到 main.py
- [ ] 前端修复 OAuth 跳转和回调处理

---

#### 后端任务清单

##### T-B01：修复 TenantContext 并发安全漏洞（P0-3）⚡ 30分钟

**文件**：`backend/app/core/tenant.py`

**修改内容**：
```python
# 将类变量改为 ContextVar
from contextvars import ContextVar

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

**验收标准**：
- [ ] 并发 10 个请求，tenant_id 不发生串行
- [ ] 运行 `pytest tests/test_tenant_context.py -v`

**负责人**：后端  
**状态**：⬜ 待开始

---

##### T-B02：创建 SQLite Mock 层基础设施 ⚡ 2小时

**新建文件**：
- `backend/app/mock/__init__.py`（空文件）
- `backend/app/mock/mock_db.py`（SQLite 异步连接）
- `backend/app/mock/schema.sql`（Mock 表结构）
- `backend/app/mock/seed.py`（Mock 数据生成）

**mock_db.py 实现**：
```python
"""
SQLite Mock 数据层
使用 aiosqlite 提供异步 SQLite 连接，用于快速联调
"""
import aiosqlite
from contextlib import asynccontextmanager
from pathlib import Path

# Mock 数据库文件路径
MOCK_DB_PATH = Path(__file__).parent.parent.parent / "mock_data.sqlite3"


@asynccontextmanager
async def get_mock_db():
    """
    获取 SQLite Mock 数据库连接（上下文管理器）
    
    Usage:
        async with get_mock_db() as db:
            cursor = await db.execute("SELECT * FROM mock_dashboard_trend")
            rows = await cursor.fetchall()
    """
    async with aiosqlite.connect(MOCK_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def init_mock_db():
    """
    初始化 Mock 数据库
    
    1. 创建表结构（执行 schema.sql）
    2. 生成初始数据（星海教育演示数据）
    """
    schema_path = Path(__file__).parent / "schema.sql"
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema 文件不存在: {schema_path}")
    
    async with get_mock_db() as db:
        # 执行建表语句
        with open(schema_path, "r", encoding="utf-8") as f:
            await db.executescript(f.read())
        await db.commit()
    
    # 生成演示数据
    await seed_demo_data()


async def seed_demo_data():
    """生成"星海教育"演示数据"""
    from .seed import generate_all_demo_data
    await generate_all_demo_data()


def is_mock_mode() -> bool:
    """检查是否启用 Mock 模式"""
    import os
    return os.getenv("MOCK_MODE", "false").lower() == "true"
```

**schema.sql 实现**：
```sql
-- 演示仪表盘趋势数据（30天）
CREATE TABLE IF NOT EXISTS mock_dashboard_trend (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    date TEXT NOT NULL,
    spend REAL DEFAULT 0,
    leads INTEGER DEFAULT 0,
    deals INTEGER DEFAULT 0,
    deal_amount REAL DEFAULT 0,
    platform TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_trend_tenant_date 
    ON mock_dashboard_trend(tenant_id, date);

-- 演示线索数据
CREATE TABLE IF NOT EXISTS mock_crm_leads (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    batch_id TEXT,
    name TEXT,
    phone_masked TEXT,
    phone_hash TEXT,
    source_channel TEXT,
    course_name TEXT,
    deal_status TEXT DEFAULT 'following',
    deal_amount REAL DEFAULT 0,
    attribution_rule_id TEXT,
    created_at TEXT,
    updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_leads_tenant ON mock_crm_leads(tenant_id);
CREATE INDEX IF NOT EXISTS idx_leads_batch ON mock_crm_leads(batch_id);

-- 导入批次记录
CREATE TABLE IF NOT EXISTS mock_crm_batches (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    filename TEXT,
    total_rows INTEGER DEFAULT 0,
    processed_rows INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    mapping_confirmed INTEGER DEFAULT 0,
    attribution_confirmed INTEGER DEFAULT 0,
    created_at TEXT,
    completed_at TEXT
);

-- 演示报表
CREATE TABLE IF NOT EXISTS mock_reports (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    report_type TEXT,
    date_range_start TEXT,
    date_range_end TEXT,
    status TEXT DEFAULT 'ready',
    file_path TEXT,
    insights TEXT,
    created_at TEXT
);

-- 引导状态
CREATE TABLE IF NOT EXISTS mock_onboarding (
    tenant_id TEXT PRIMARY KEY,
    step1_done INTEGER DEFAULT 0,
    step1_org_name TEXT,
    step1_industry TEXT,
    step2_done INTEGER DEFAULT 0,
    step3_done INTEGER DEFAULT 0,
    completed_at TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 归因规则
CREATE TABLE IF NOT EXISTS mock_attribution_rules (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    name TEXT,
    platform TEXT,
    keywords TEXT,
    priority INTEGER DEFAULT 0,
    created_at TEXT
);
```

**seed.py 实现**：
```python
"""
Mock 数据生成脚本
生成"星海教育"演示数据集
"""
import random
from datetime import datetime, timedelta
from pathlib import Path

DEMO_CONFIG = {
    "org_name": "星海教育",
    "industry": "K12教育",
    "daily_spend_range": (8000, 15000),
    "cpe_range": (30, 50),
    "roi_range": (3.0, 6.0),
    "juliang_spend_ratio": 0.6,
    "baidu_spend_ratio": 0.4,
    "total_leads_30d": 1200,
    "deal_rate": 0.18,
    "courses": ["小学数学", "初中英语", "高中物理", "少儿编程"],
    "channels": ["抖音", "百度", "微信朋友圈", "知乎"],
}


async def generate_all_demo_data():
    """生成全套演示数据"""
    from .mock_db import get_mock_db
    
    # 使用固定的 tenant_id（演示专用）
    demo_tenant_id = "ten_demo_xinghai"
    
    async with get_mock_db() as db:
        # 1. 生成 30 天趋势数据
        await _generate_30d_trend(db, demo_tenant_id)
        
        # 2. 生成 500 条线索
        await _generate_crm_leads(db, demo_tenant_id)
        
        # 3. 生成 3 份报表
        await _generate_reports(db, demo_tenant_id)
        
        # 4. 初始化引导状态
        await _init_onboarding(db, demo_tenant_id)
        
        # 5. 生成归因规则
        await _generate_attribution_rules(db, demo_tenant_id)
        
        await db.commit()


async def _generate_30d_trend(db, tenant_id: str):
    """生成30天仪表盘数据"""
    base_date = datetime.now() - timedelta(days=30)
    
    for i in range(30):
        date = base_date + timedelta(days=i)
        
        # 抖音数据 (60%)
        jl_spend = random.uniform(4800, 9000)
        jl_leads = int(jl_spend / random.uniform(30, 50))
        
        # 百度数据 (40%)
        bd_spend = random.uniform(3200, 6000)
        bd_leads = int(bd_spend / random.uniform(35, 55))
        
        total_spend = jl_spend + bd_spend
        total_leads = jl_leads + bd_leads
        total_deals = int(total_leads * 0.18)
        total_deal_amount = total_deals * random.uniform(4000, 6000)
        
        await db.execute(
            """INSERT INTO mock_dashboard_trend 
               (tenant_id, date, spend, leads, deals, deal_amount, platform)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (tenant_id, date.strftime("%Y-%m-%d"), 
             round(total_spend, 2), total_leads, total_deals, 
             round(total_deal_amount, 2), "combined")
        )


async def _generate_crm_leads(db, tenant_id: str):
    """生成500条模拟线索"""
    import secrets
    
    for i in range(500):
        name = f"学员{random.choice(['张', '李', '王', '赵', '刘'])}{random.randint(1, 100)}"
        phone_suffix = random.randint(10000000, 99999999)
        
        await db.execute(
            """INSERT INTO mock_crm_leads 
               (id, tenant_id, name, phone_masked, source_channel, 
                course_name, deal_status, deal_amount, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                f"lead_{secrets.token_hex(8)}",
                tenant_id,
                name,
                f"138****{phone_suffix % 10000:04d}",
                random.choice(DEMO_CONFIG["channels"]),
                random.choice(DEMO_CONFIG["courses"]),
                random.choices(
                    ["deal", "no_deal", "following"], 
                    weights=[0.18, 0.42, 0.40]
                )[0],
                random.uniform(3000, 8000) if random.random() < 0.18 else 0,
                (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
            )
        )


async def _generate_reports(db, tenant_id: str):
    """生成3份演示报表"""
    import secrets
    
    report_types = ["daily", "weekly", "monthly"]
    for i, rtype in enumerate(report_types):
        await db.execute(
            """INSERT INTO mock_reports
               (id, tenant_id, report_type, date_range_start, date_range_end,
                status, insights, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                f"report_{secrets.token_hex(8)}",
                tenant_id,
                rtype,
                (datetime.now() - timedelta(days=(i+1)*10)).strftime("%Y-%m-%d"),
                datetime.now().strftime("%Y-%m-%d"),
                "ready",
                '["建议增加抖音短视频投放预算", "百度关键词ROI下降，建议优化着陆页", "周末转化率提升20%"]',
                datetime.now().isoformat()
            )
        )


async def _init_onboarding(db, tenant_id: str):
    """初始化引导状态"""
    await db.execute(
        """INSERT OR REPLACE INTO mock_onboarding
           (tenant_id, step1_done, step1_org_name, step1_industry)
           VALUES (?, ?, ?, ?)""",
        (tenant_id, 0, DEMO_CONFIG["org_name"], DEMO_CONFIG["industry"])
    )


async def _generate_attribution_rules(db, tenant_id: str):
    """生成归因规则"""
    import secrets
    
    rules = [
        {"name": "抖音咨询归因", "platform": "juliang", "keywords": '["咨询", "开口", "留资"]'},
        {"name": "百度搜索归因", "platform": "baidu", "keywords": '["报名", "咨询", "价格"]'},
        {"name": "微信社群归因", "platform": "wechat", "keywords": '["微课", "资料", "体验课"]'},
    ]
    
    for rule in rules:
        await db.execute(
            """INSERT INTO mock_attribution_rules
               (id, tenant_id, name, platform, keywords, priority, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                f"attr_{secrets.token_hex(8)}",
                tenant_id,
                rule["name"],
                rule["platform"],
                rule["keywords"],
                random.randint(1, 10),
                datetime.now().isoformat()
            )
        )
```

**验收标准**：
- [ ] `python -c "from app.mock.mock_db import init_mock_db; import asyncio; asyncio.run(init_mock_db())"` 执行成功
- [ ] `mock_data.sqlite3` 生成在 backend/ 目录
- [ ] SQLite 中 6 张表全部创建成功
- [ ] 数据验证：30 天趋势行 × 1，500 条线索，3 份报表

**负责人**：后端  
**状态**：⬜ 待开始

---

##### T-B03：创建 auth.py 认证路由（真实逻辑）⚡ 3小时

**新建文件**：
- `backend/app/api/v1/auth.py`
- `backend/app/schemas/auth.py`

**实现内容**：见 `phase1-sprint-technical-spec.md` 3.3 节

**接口列表**：
| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /auth/register | 注册（创建 Tenant + User） |
| POST | /auth/login | 登录（签发 JWT） |
| POST | /auth/logout | 登出（Token 黑名单） |
| POST | /auth/refresh | 刷新 Token |
| GET | /auth/profile | 获取用户信息 |

**验收标准**：
- [ ] `POST /auth/register` 返回 201 + JWT
- [ ] MySQL `users` 表和 `tenants` 表有数据写入
- [ ] `POST /auth/login` 返回正确 Token
- [ ] `GET /auth/profile` 需要 Bearer Token，返回用户信息
- [ ] `POST /auth/refresh` 使用 refresh_token 换取新 access_token

**负责人**：后端  
**状态**：⬜ 待开始

---

##### T-B04：注册所有路由到 main.py ⚡ 30分钟

**修改文件**：`backend/app/main.py`

**修改内容**：
```python
# 在文件顶部添加导入
from app.api.v1.auth import router as auth_router
from app.api.v1.demo import router as demo_router
from app.api.v1.onboarding import router as onboarding_router
from app.api.v1.crm import router as crm_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.reports import router as reports_router
from app.api.v1.settings import router as settings_router

# 在文件末尾（路由注册区域）添加
# 认证路由
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)

# 演示数据路由 (Mock)
app.include_router(demo_router, prefix=settings.API_V1_PREFIX)

# 引导向导路由 (Mock)
app.include_router(onboarding_router, prefix=settings.API_V1_PREFIX)

# CRM 路由 (混合)
app.include_router(crm_router, prefix=settings.API_V1_PREFIX)

# 数据分析路由 (Mock)
app.include_router(analytics_router, prefix=settings.API_V1_PREFIX)

# 报表路由 (Mock)
app.include_router(reports_router, prefix=settings.API_V1_PREFIX)

# 设置路由 (混合)
app.include_router(settings_router, prefix=settings.API_V1_PREFIX)
```

**注意**：如果某些路由文件尚未创建，可以先用占位路由（返回 501），确保服务能启动。

**验收标准**：
- [ ] `uvicorn app.main:app --reload` 启动无报错
- [ ] 访问 `/docs` 能看到所有 8 个模块接口
- [ ] 所有接口都有响应（哪怕是 501）

**负责人**：后端  
**状态**：⬜ 待开始

---

#### 前端任务清单

##### T-F01：修复 OAuth window.open → window.location.href（P1-1）⚡ 10分钟

**修改文件**：`frontend-web/src/pages/ad-accounts/index.tsx`

**修改内容**：
```typescript
// 找到 OAuth 跳转代码，将 window.open 改为 window.location.href
// 修改前：
// window.open(oauthUrl, '_blank');

// 修改后：
window.location.href = oauthUrl;  // 整页跳转，避免弹窗被拦截
```

**验收标准**：
- [ ] 点击"绑定巨量引擎"或"绑定百度"时，整页跳转到授权页
- [ ] 不再打开新窗口

**负责人**：前端  
**状态**：⬜ 待开始

---

##### T-F02：补全 OAuth 回调结果处理（P1-6）⚡ 20分钟

**修改文件**：`frontend-web/src/pages/ad-accounts/index.tsx`

**修改内容**：
```typescript
// 在 useEffect 中读取 URL 参数 oauth_result
useEffect(() => {
  const params = new URLSearchParams(window.location.search);
  const oauthResult = params.get('oauth_result');
  const platform = params.get('platform');
  const accountName = params.get('account_name');
  
  if (oauthResult === 'success') {
    toast.success(`${platform === 'baidu' ? '百度' : '巨量引擎'}账户 ${accountName} 绑定成功！`);
    // 清除 URL 参数
    window.history.replaceState({}, '', '/ad-accounts');
    // 刷新账户列表
    refreshAccounts();
  } else if (oauthResult === 'cancelled') {
    toast.info('授权已取消');
    window.history.replaceState({}, '', '/ad-accounts');
  } else if (oauthResult === 'error') {
    const reason = params.get('reason');
    toast.error(`授权失败: ${reason}`);
    window.history.replaceState({}, '', '/ad-accounts');
  }
}, []);
```

**验收标准**：
- [ ] OAuth 回调后显示 Toast 提示
- [ ] URL 参数被清除（地址栏干净）
- [ ] 成功/取消/失败三种状态都有正确处理

**负责人**：前端  
**状态**：⬜ 待开始

---

### Day 2（2026-04-29）：认证联调 + 百度 OAuth 路由

#### 🎯 当日目标
- [ ] 完善 auth.py 并联调
- [ ] 百度 OAuth 回调完整验证
- [ ] 创建 onboarding.py 路由（Mock）
- [ ] 前端登录/注册页面联调
- [ ] 修复 dashboard timeRange parseInt 问题

---

#### 后端任务清单

##### T-B05：完善 auth.py 并联调 ⚡ 2小时

**文件**：`backend/app/api/v1/auth.py`

**补充内容**：

1. **登出实现**（Token 黑名单）：
```python
@router.post("/logout")
async def logout(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
):
    """用户登出 - Token 加入黑名单"""
    if not credentials:
        raise HTTPException(status_code=401, detail="未提供 Token")
    
    token = credentials.credentials
    payload = verify_access_token(token)
    
    if payload:
        # 计算 Token 剩余有效期
        exp = payload.get("exp", 0)
        ttl = max(exp - datetime.now(timezone.utc).timestamp(), 0)
        
        # 加入黑名单（使用 jti 或 token 哈希）
        await add_token_to_blacklist(token, int(ttl))
    
    return {"message": "登出成功"}
```

2. **Token 刷新完善**：
```python
@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(req: RefreshTokenRequest):
    """刷新 Access Token"""
    payload = verify_refresh_token(req.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token 无效或已过期"
        )
    
    # 验证 refresh_token 未被加入黑名单
    if await is_token_blacklisted(req.refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token 已失效"
        )
    
    # 签发新的 Access Token
    new_access_token = create_access_token(
        data={"sub": payload["sub"], "tenant_id": payload["tenant_id"]}
    )
    
    return LoginResponse(
        access_token=new_access_token,
        refresh_token=req.refresh_token,  # 保持原 refresh_token
        token_type="bearer",
        user=...  # 需要从数据库查询
    )
```

**验收标准**：
- [ ] 使用注册返回的 Token 访问 `/auth/profile` 成功
- [ ] 登出后 Token 立即失效（访问返回 401）
- [ ] Refresh Token 可以换取新的 Access Token

**负责人**：后端  
**状态**：⬜ 待开始

---

##### T-B06：百度 OAuth 路由验证 ⚡ 2小时

**文件**：`backend/app/api/v1/ad_accounts.py`（已有，验证完整性）

**验证清单**：
- [ ] `GET /ad/baidu/oauth-url` 返回授权 URL
- [ ] `GET /baidu/callback` 正确处理 code 和 state
- [ ] Token 换取逻辑调用 `baidu_service.exchange_token(code)`
- [ ] 绑定成功后触发 Celery 任务 `sync_ad_data_baidu.delay(ad_account.id, days=7)`
- [ ] 重定向到前端 `/ad-accounts?oauth_result=success&platform=baidu&...`

**发现问题时的修复**：
```python
# 如果 baidu_service 缺少方法，需要在 baidu_service.py 中补充
# 检查文件：backend/app/services/baidu_service.py
```

**验收标准**：
- [ ] 完整的 OAuth 流程可以在浏览器中走通
- [ ] Celery Worker 日志中能看到任务被触发

**负责人**：后端  
**状态**：⬜ 待开始

---

##### T-B07：onboarding.py 路由（SQLite Mock）⚡ 1.5小时

**新建文件**：
- `backend/app/api/v1/onboarding.py`
- `backend/app/schemas/onboarding.py`

**onboarding.py 实现**：
```python
"""
引导向导 API 路由
使用 SQLite Mock 存储引导进度
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import get_current_user
from app.mock.mock_db import get_mock_db

router = APIRouter(prefix="/onboarding", tags=["引导向导"])


@router.get("/status")
async def get_onboarding_status(
    current_user: dict = Depends(get_current_user),
):
    """获取引导进度"""
    async with get_mock_db() as db:
        cursor = await db.execute(
            "SELECT * FROM mock_onboarding WHERE tenant_id = ?",
            (current_user["tenant_id"],)
        )
        row = await cursor.fetchone()
        
        if row:
            return {
                "step1_done": bool(row["step1_done"]),
                "step1_org_name": row["step1_org_name"],
                "step1_industry": row["step1_industry"],
                "step2_done": bool(row["step2_done"]),
                "step3_done": bool(row["step3_done"]),
                "completed": all([
                    bool(row["step1_done"]),
                    bool(row["step2_done"]),
                    bool(row["step3_done"]),
                ])
            }
        
        return {
            "step1_done": False,
            "step1_org_name": None,
            "step1_industry": None,
            "step2_done": False,
            "step3_done": False,
            "completed": False
        }


@router.post("/status")
async def update_onboarding_status(
    body: dict,  # 简化：直接接收字典
    current_user: dict = Depends(get_current_user),
):
    """更新引导进度"""
    async with get_mock_db() as db:
        # UPSERT 逻辑
        await db.execute(
            """INSERT INTO mock_onboarding 
               (tenant_id, step1_done, step1_org_name, step1_industry, updated_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(tenant_id) DO UPDATE SET
               step1_done=excluded.step1_done,
               step1_org_name=excluded.step1_org_name,
               step1_industry=excluded.step1_industry,
               updated_at=excluded.updated_at""",
            (
                current_user["tenant_id"],
                1 if body.get("step1_done") else 0,
                body.get("step1_org_name"),
                body.get("step1_industry"),
                datetime.now().isoformat()
            )
        )
        await db.commit()
    
    return {"message": "引导进度已更新"}


@router.post("/complete")
async def complete_onboarding(
    current_user: dict = Depends(get_current_user),
):
    """标记引导全部完成"""
    async with get_mock_db() as db:
        await db.execute(
            """UPDATE mock_onboarding 
               SET step1_done=1, step2_done=1, step3_done=1,
                   completed_at=?, updated_at=?
               WHERE tenant_id=?""",
            (datetime.now().isoformat(), datetime.now().isoformat(),
             current_user["tenant_id"])
        )
        await db.commit()
    
    return {"message": "引导已完成"}
```

**验收标准**：
- [ ] `GET /onboarding/status` 返回引导状态
- [ ] `POST /onboarding/status` 更新步骤 1 数据
- [ ] `POST /onboarding/complete` 标记完成

**负责人**：后端  
**状态**：⬜ 待开始

---

#### 前端任务清单

##### T-F03：登录/注册页面联调 ⚡ 1.5小时

**文件**：`frontend-web/src/pages/login/index.tsx`, `frontend-web/src/stores/authStore.ts`

**检查清单**：
- [ ] `authStore.login()` 调用 `POST /auth/login`
- [ ] `authStore.register()` 调用 `POST /auth/register`
- [ ] `authStore.logout()` 调用 `POST /auth/logout`
- [ ] Token 存储到 localStorage
- [ ] 请求头自动携带 `Authorization: Bearer {token}`

**修改示例**（如果 store 中接口路径不对）：
```typescript
// frontend-web/src/stores/authStore.ts
const response = await api.post('/auth/login', {
  email: credentials.email,
  password: credentials.password,
});
```

**验收标准**：
- [ ] 注册新用户成功，自动跳转
- [ ] 登录成功，Token 存储
- [ ] 访问受保护页面（如 /dashboard）不再 401

**负责人**：前端  
**状态**：⬜ 待开始

---

##### T-F04：修复 timeRange parseInt 问题（P1-3）⚡ 10分钟

**文件**：`frontend-web/src/pages/dashboard/index.tsx`

**修改内容**：
```typescript
// 找到 timeRange 相关的 Select 组件
// 修改前：
// <Select value={timeRange.toString()} ...>

// 修改后：将 options 的 value 直接改为数字
const timeRangeOptions = [
  { label: '最近7天', value: 7 },      // 之前可能是 '7'
  { label: '最近30天', value: 30 },
  { label: '最近90天', value: 90 },
];

// 使用时无需 parseInt
const days = timeRange;  // 已经是数字
```

**验收标准**：
- [ ] 选择时间范围后，API 请求参数正确（数字类型）
- [ ] 仪表盘数据按选定范围加载

**负责人**：前端  
**状态**：⬜ 待开始

---

### Day 3（2026-04-30）：Mock 层填充 + 仪表盘/演示数据联调

#### 🎯 当日目标
- [ ] 创建 demo.py 路由（Mock）
- [ ] 创建 analytics.py 路由（Mock）
- [ ] 创建 settings.py 路由（Mock + 真实混合）
- [ ] 前端演示数据 + 仪表盘联调
- [ ] 修复 P2 系列前端问题

---

#### 后端任务清单

##### T-B08：demo.py 路由（SQLite Mock）⚡ 1.5小时

**新建文件**：`backend/app/api/v1/demo.py`, `backend/app/schemas/demo.py`

**实现内容**：
```python
"""
演示数据 API 路由
返回"星海教育"固定演示数据集
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime

from app.core.tenant import get_current_user
from app.mock.mock_db import get_mock_db

router = APIRouter(prefix="/demo", tags=["演示数据"])


class DemoDashboardResponse(BaseModel):
    """演示仪表盘响应"""
    org_name: str = "星海教育"
    total_spend: float
    total_leads: int
    total_deals: int
    total_deal_amount: float
    cpe: float  # 线索成本
    roi: float
    deal_rate: float
    trend: list[dict]


@router.get("/dashboard", response_model=DemoDashboardResponse)
async def get_demo_dashboard(
    current_user: dict = Depends(get_current_user),
):
    """获取演示仪表盘数据"""
    async with get_mock_db() as db:
        # 聚合计算核心指标
        cursor = await db.execute(
            """SELECT 
                SUM(spend) as total_spend,
                SUM(leads) as total_leads,
                SUM(deals) as total_deals,
                SUM(deal_amount) as total_deal_amount
               FROM mock_dashboard_trend 
               WHERE tenant_id = ?""",
            ("ten_demo_xinghai",)
        )
        row = await cursor.fetchone()
        
        total_spend = row["total_spend"] or 0
        total_leads = row["total_leads"] or 0
        total_deals = row["total_deals"] or 0
        total_deal_amount = row["total_deal_amount"] or 0
        
        # 获取趋势数据
        trend_cursor = await db.execute(
            """SELECT date, spend, leads, deals, deal_amount 
               FROM mock_dashboard_trend 
               WHERE tenant_id = ? 
               ORDER BY date""",
            ("ten_demo_xinghai",)
        )
        trend_rows = await trend_cursor.fetchall()
        trend = [dict(r) for r in trend_rows]
        
        return DemoDashboardResponse(
            total_spend=round(total_spend, 2),
            total_leads=total_leads,
            total_deals=total_deals,
            total_deal_amount=round(total_deal_amount, 2),
            cpe=round(total_spend / total_leads, 2) if total_leads > 0 else 0,
            roi=round(total_deal_amount / total_spend, 2) if total_spend > 0 else 0,
            deal_rate=round(total_deals / total_leads * 100, 2) if total_leads > 0 else 0,
            trend=trend
        )
```

**验收标准**：
- [ ] `GET /demo/dashboard` 返回"星海教育"演示数据
- [ ] 数据包含总花费、线索数、成交数、ROI 等
- [ ] 趋势数据包含 30 天的详细记录

**负责人**：后端  
**状态**：⬜ 待开始

---

##### T-B09：analytics.py 路由（SQLite Mock）⚡ 3小时

**新建文件**：`backend/app/api/v1/analytics.py`, `backend/app/schemas/analytics.py`

**接口清单**：
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /analytics/dashboard | 仪表盘核心指标 |
| GET | /analytics/dashboard/status | 数据就绪状态 |
| GET | /analytics/trend | 30天趋势 |
| GET | /analytics/channel-compare | 渠道对比 |
| GET | /analytics/cross-table | 交叉分析 |
| GET | /analytics/cross-table/export | 导出 CSV |

**实现要点**：
- 从 SQLite Mock 读取数据
- `/analytics/dashboard/status` 需要查询真实 MySQL（是否有广告账户）
- 聚合计算 ROI、CPE、成交率等指标

**验收标准**：
- [ ] 所有接口返回 Mock 数据（非 404）
- [ ] 仪表盘状态检查正确
- [ ] 趋势数据包含日期、花费、线索等

**负责人**：后端  
**状态**：⬜ 待开始

---

##### T-B10：settings.py 路由（SQLite Mock + 真实混合）⚡ 1.5小时

**新建文件**：`backend/app/api/v1/settings.py`, `backend/app/schemas/settings.py`

**接口清单**：
| 方法 | 路径 | 描述 | 类型 |
|------|------|------|------|
| GET | /settings/tenant | 租户信息 | REAL |
| PATCH | /settings/tenant | 更新租户信息 | REAL |
| GET | /settings/attribution-rules | 归因规则列表 | MOCK |
| POST | /settings/attribution-rules | 创建规则 | MOCK |
| PATCH | /settings/attribution-rules/{id} | 更新规则 | MOCK |
| DELETE | /settings/attribution-rules/{id} | 删除规则 | MOCK |

**验收标准**：
- [ ] 租户信息从 MySQL 真实返回
- [ ] 归因规则从 SQLite Mock 返回

**负责人**：后端  
**状态**：⬜ 待开始

---

#### 前端任务清单

##### T-F05：演示数据 + 仪表盘联调 ⚡ 2小时

**文件**：`frontend-web/src/stores/demoStore.ts`, `frontend-web/src/pages/dashboard/index.tsx`

**检查清单**：
- [ ] `demoStore.enableDemoMode()` 调用 `GET /demo/dashboard`
- [ ] Dashboard 正确显示演示数据角标（蓝色"演示模式"）
- [ ] `GET /analytics/dashboard` 返回数据并渲染图表
- [ ] `GET /analytics/dashboard/status` 正确判定是否有数据

**修复 P2 系列问题**：
- [ ] P2-2：EmptyState scenario 类型对齐
- [ ] P2-7：`enableDemoMode` 解构方式

**验收标准**：
- [ ] 演示模式切换正常工作
- [ ] 仪表盘图表正确渲染
- [ ] 空状态提示正确显示

**负责人**：前端  
**状态**：⬜ 待开始

---

### Day 4（2026-05-01）：CRM 路由 + 报表路由 Mock

#### 🎯 当日目标
- [ ] 创建 crm.py 路由（真实 + Mock 混合）
- [ ] 创建 reports.py 路由（Mock）
- [ ] 前端 CRM 页面 Bug 修复
- [ ] CRM 页面联调验收

---

#### 后端任务清单

##### T-B11：crm.py 路由（真实 + Mock 混合）⚡ 4小时

**新建文件**：
- `backend/app/api/v1/crm.py`
- `backend/app/schemas/crm.py`
- `backend/app/models/crm_lead.py`（基础 ORM）

**实现策略**：

| 功能 | 实现方式 |
|------|----------|
| POST /crm/upload | REAL（保存文件，触发 Celery） |
| GET /crm/upload/{task_id} | REAL（Redis 查询进度） |
| POST /crm/upload/{batch_id}/preview | MOCK |
| POST /crm/upload/{batch_id}/confirm | MOCK |
| GET /crm/upload/{batch_id}/attribution-suggest | MOCK |
| GET /crm/leads | MOCK |
| PATCH /crm/leads/{id} | MOCK |
| GET /crm/batches | MOCK |
| DELETE /crm/batches/{id} | MOCK |

**crm.py 核心实现**：
```python
"""
CRM 导入 API 路由
混合实现：文件上传用真实，数据查询用 Mock
"""
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import get_current_user
from app.mock.mock_db import get_mock_db

router = APIRouter(prefix="/crm", tags=["CRM 导入"])


@router.post("/upload")
async def upload_crm_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """上传 CRM Excel 文件"""
    # 保存文件到临时目录
    import os
    temp_dir = "/tmp/crm_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    
    file_path = os.path.join(temp_dir, f"{current_user['tenant_id']}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # 触发 Celery 任务（占位）
    # from app.tasks.import_tasks import process_crm_file
    # task = process_crm_file.delay(file_path, current_user['tenant_id'])
    task_id = "mock_task_123"  # 模拟 task_id
    
    # 创建 Mock 批次记录
    import secrets
    batch_id = f"batch_{secrets.token_hex(8)}"
    async with get_mock_db() as db:
        await db.execute(
            """INSERT INTO mock_crm_batches 
               (id, tenant_id, filename, status, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (batch_id, current_user["tenant_id"], file.filename, 
             "processing", datetime.now().isoformat())
        )
        await db.commit()
    
    return {
        "batch_id": batch_id,
        "task_id": task_id,
        "message": "文件上传成功，正在处理..."
    }


@router.get("/leads")
async def list_crm_leads(
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
):
    """线索列表（Mock）"""
    async with get_mock_db() as db:
        cursor = await db.execute(
            """SELECT * FROM mock_crm_leads 
               WHERE tenant_id = ? 
               LIMIT ? OFFSET ?""",
            (current_user["tenant_id"], page_size, (page-1)*page_size)
        )
        rows = await cursor.fetchall()
        leads = [dict(r) for r in rows]
        
        # 总数
        count_cursor = await db.execute(
            "SELECT COUNT(*) FROM mock_crm_leads WHERE tenant_id = ?",
            (current_user["tenant_id"],)
        )
        total = (await count_cursor.fetchone())[0]
        
        return {"items": leads, "total": total, "page": page, "page_size": page_size}
```

**验收标准**：
- [ ] `POST /crm/upload` 接收文件并返回 batch_id
- [ ] `GET /crm/leads` 返回 Mock 线索列表
- [ ] 分页参数正常工作

**负责人**：后端  
**状态**：⬜ 待开始

---

##### T-B12：reports.py 路由（SQLite Mock）⚡ 2小时

**新建文件**：`backend/app/api/v1/reports.py`, `backend/app/schemas/report.py`

**接口清单**：
| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /reports/generate | 生成报表 |
| GET | /reports | 报表列表 |
| GET | /reports/{id} | 报表详情 |
| GET | /reports/{id}/download | 下载报表 |
| GET | /reports/{id}/insights | 行动建议 |

**events.py 实现要点**：
- 生成报表：Mock 立即返回 task_id，状态为 "ready"
- 报表列表：从 SQLite Mock 读取
- 下载：返回示例 Excel bytes（或文件路径）
- 行动建议：返回固定的 3 条建议

**验收标准**：
- [ ] 所有接口返回非 404
- [ ] 报表列表包含演示数据中的 3 份报表
- [ ] 行动建议返回 3 条建议

**负责人**：后端  
**状态**：⬜ 待开始

---

#### 前端任务清单

##### T-F06：修复 CRM beforeUpload + previewMapping（P1-4, P1-5）⚡ 1.5小时

**文件**：`frontend-web/src/pages/crm/index.tsx`

**修改内容**：

1. **删除 beforeUpload={() => false}**：
```typescript
// 修改前：
<Upload beforeUpload={() => false} ...>

// 修改后：移除 beforeUpload，让请求正常发送
<Upload ...>
```

2. **previewMapping 改为 POST 请求**：
```typescript
// 修改前可能是 GET 或其他方式，改为：
const response = await api.post(`/crm/upload/${batchId}/preview`, {
  mapping: mappingData
});
```

3. **修复弹窗显示逻辑顺序**：
```typescript
// 确保字段映射弹窗先于归因确认弹窗显示
if (showFieldMapping) {
  // 显示字段映射
} else if (showAttribution) {
  // 显示归因确认
}
```

**验收标准**：
- [ ] 文件上传正常触发
- [ ] 字段预览请求正确（POST）
- [ ] 弹窗顺序正确：先映射，后归因

**负责人**：前端  
**状态**：⬜ 待开始

---

##### T-F07：CRM 页面联调验收 ⚡ 1小时

**测试流程**：
1. 上传 Excel 文件
2. 轮询进度（`GET /crm/upload/{task_id}`）
3. 显示字段映射弹窗
4. 确认映射后显示归因确认弹窗
5. 确认归因后刷新线索列表

**验收标准**：
- [ ] 完整流程可以走通
- [ ] 前端状态管理与后端接口对接正确
- [ ] 错误处理正确（上传失败、网络错误等）

**负责人**：前端  
**状态**：⬜ 待开始

---

### Day 5（2026-05-02）：集成联调 + BUG 修复 + 冒烟测试

#### 🎯 当日目标
- [ ] 注册所有路由到 main.py（最终检查）
- [ ] 异常处理完善（自定义 Exception Handler）
- [ ] 统一 UTC 时间
- [ ] OAuth state 验证加固
- [ ] 全流程冒烟测试
- [ ] Token 刷新并发锁

---

#### 后端任务清单

##### T-B13：注册所有路由 + 异常处理完善（P3-2）⚡ 1小时

**文件**：`backend/app/main.py`, `backend/app/core/exceptions.py`

**全局异常处理**：
```python
# backend/app/main.py

from app.core.exceptions import EduAdCRMException

@app.exception_handler(EduAdCRMException)
async def eduaacrm_exception_handler(request: Request, exc: EduAdCRMException):
    """EduAdCRM 业务异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.detail,
            "extra": exc.extra if exc.extra else None,
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
```

**统一 UTC 时间**：
```python
# backend/app/core/database.py 或 config.py 中设置
# 确保所有 datetime 都使用 UTC
from datetime import datetime, timezone

def utc_now():
    """获取当前 UTC 时间"""
    return datetime.now(timezone.utc)
```

**验收标准**：
- [ ] 所有 8 个路由已注册，`/docs` 可见
- [ ] 业务异常返回统一格式（code, message, extra）
- [ ] 数据库时间存储为 UTC

**负责人**：后端  
**状态**：⬜ 待开始

---

##### T-B14：OAuth state 验证加固（P2-1）⚡ 30分钟

**文件**：`backend/app/api/v1/ad_accounts.py`

**修改内容**：
```python
# 在生产环境中，禁止无 state 的 OAuth 回调降级

@router.get("/juliang/callback")
async def juliang_oauth_callback(
    ...,
    state: Optional[str] = Query(None, ...),
):
    # 生产环境强制要求 state
    if not state:
        logger.warning("生产环境拒绝无 state 的 OAuth 回调")
        # 根据环境变量决定是否允许降级
        if os.getenv("ALLOW_OAUTH_STATE_DOWNGRADE", "false").lower() != "true":
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/ad-accounts?oauth_result=error&reason=missing_state",
                status_code=302,
            )
    
    # 原有逻辑...
```

**验收标准**：
- [ ] 无 state 参数时，根据环境变量决定是否允许降级
- [ ] 生产环境（ALLOW_OAUTH_STATE_DOWNGRADE=false）拒绝无 state 请求

**负责人**：后端  
**状态**：⬜ 待开始

---

#### 前端任务清单

##### T-F08：全流程冒烟测试 ⚡ 2小时

**测试场景清单**：

**场景 1：新租户注册流程**
1. 访问 `/login`，点击"注册"
2. 填写邮箱、密码、机构名称
3. 提交注册 → 期望：201，返回 Token
4. 自动跳转到引导向导 `/onboarding`

**场景 2：引导向导**
1. 步骤 1：填写机构信息 → `POST /onboarding/status`
2. 步骤 2：点击"绑定百度" → 跳转授权页
3. 完成授权 → 回调 `/ad-accounts?oauth_result=success`
4. 步骤 3：上传 CRM 文件 → `POST /crm/upload`
5. 完成引导 → `POST /onboarding/complete`

**场景 3：仪表盘**
1. 切换到"演示模式" → `GET /demo/dashboard`
2. 查看真实数据（如果有广告账户） → `GET /analytics/dashboard`

**场景 4：CRM 导入**
1. 上传 Excel → 进度轮询 → 字段映射 → 归因确认
2. 线索列表刷新 → 查看导入的线索

**场景 5：登出**
1. 点击登出 → `POST /auth/logout`
2. 尝试访问受保护接口 → 期望 401

**验收标准**：
- [ ] 所有场景测试通过
- [ ] 并记录发现的问题到 BUG 清单

**负责人**：前端  
**状态**：⬜ 待开始

---

##### T-F09：Token 刷新并发锁（P3-1）⚡ 30分钟

**文件**：`frontend-web/src/api/request.ts`

**修改内容**：
```typescript
// 添加 refreshPromise 锁避免并发刷新
let refreshPromise: Promise<string> | null = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      // 如果没有正在刷新的 Promise，就创建一个
      if (!refreshPromise) {
        refreshPromise = api.post('/auth/refresh', {
          refresh_token: localStorage.getItem('refresh_token')
        }).then((res) => {
          const newToken = res.data.access_token;
          localStorage.setItem('access_token', newToken);
          refreshPromise = null;  // 清除锁
          return newToken;
        }).catch((err) => {
          refreshPromise = null;  // 清除锁
          localStorage.clear();
          window.location.href = '/login';
          throw err;
        });
      }
      
      // 等待刷新完成
      const newToken = await refreshPromise;
      originalRequest.headers.Authorization = `Bearer ${newToken}`;
      return api(originalRequest);
    }
    
    return Promise.reject(error);
  }
);
```

**验收标准**：
- [ ] 并发多个 401 请求时，只触发一次 Token 刷新
- [ ] Token 刷新后，所有重试请求都使用新 Token

**负责人**：前端  
**状态**：⬜ 待开始

---

## 二、任务优先级矩阵

### 🔴 高优先级（阻断联调，必做）

```
┌─────────────────────────────────────────────────────────────┐
│ Day 1 必须完成                                            │
├─────────────────────────────────────────────────────────────┤
│ T-B01  TenantContext 并发修复                              │
│ T-B02  SQLite Mock 基础设施                                │
│ T-B03  auth.py 认证路由（真实）                             │
│ T-B04  路由注册到 main.py                                  │
│ T-F01  OAuth window.location.href 修复                      │
│ T-F02  OAuth 回调结果处理                                  │
└─────────────────────────────────────────────────────────────┘
```

### 🟡 中优先级（功能可演示）

```
┌─────────────────────────────────────────────────────────────┐
│ Day 2-3 完成                                               │
├─────────────────────────────────────────────────────────────┤
│ T-B05  认证路由完善联调                                    │
│ T-B06  百度 OAuth 完整流程                                 │
│ T-B07  onboarding.py Mock                                 │
│ T-B08  demo.py Mock                                       │
│ T-B09  analytics.py Mock                                  │
│ T-F03  登录注册页面联调                                    │
│ T-F05  仪表盘演示数据联调                                  │
└─────────────────────────────────────────────────────────────┘
```

### 🟢 低优先级（完整体验）

```
┌─────────────────────────────────────────────────────────────┐
│ Day 4-5 完成                                               │
├─────────────────────────────────────────────────────────────┤
│ T-B10  settings.py Mock                                   │
│ T-B11  crm.py 混合实现                                    │
│ T-B12  reports.py Mock                                    │
│ T-F06  CRM Bug 修复                                       │
│ T-F07  CRM 联调验收                                       │
│ T-F08  全流程冒烟测试                                      │
│ T-F09  Token 刷新并发锁                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、每日进度跟踪表

| 任务ID | 任务名称 | 负责人 | Day1 | Day2 | Day3 | Day4 | Day5 | 状态 |
|--------|----------|--------|------|------|------|------|------|------|
| T-B01 | TenantContext 修复 | 后端 | ⬜ | | | | | |
| T-B02 | Mock 基础设施 | 后端 | ⬜ | | | | | |
| T-B03 | auth.py 创建 | 后端 | ⬜ | | | | | |
| T-B04 | 路由注册 | 后端 | ⬜ | | | | | |
| T-B05 | auth 完善联调 | 后端 | | ⬜ | | | | |
| T-B06 | 百度 OAuth | 后端 | | ⬜ | | | | |
| T-B07 | onboarding.py | 后端 | | ⬜ | | | | |
| T-B08 | demo.py | 后端 | | | ⬜ | | | |
| T-B09 | analytics.py | 后端 | | | ⬜ | | | |
| T-B10 | settings.py | 后端 | | | ⬜ | | | |
| T-B11 | crm.py | 后端 | | | | ⬜ | | |
| T-B12 | reports.py | 后端 | | | | ⬜ | | |
| T-B13 | 异常处理完善 | 后端 | | | | | ⬜ | |
| T-B14 | OAuth state 加固 | 后端 | | | | | ⬜ | |
| T-F01 | OAuth 跳转修复 | 前端 | ⬜ | | | | | |
| T-F02 | OAuth 回调处理 | 前端 | ⬜ | | | | | |
| T-F03 | 登录注册联调 | 前端 | | ⬜ | | | | |
| T-F04 | timeRange 修复 | 前端 | | ⬜ | | | | |
| T-F05 | 仪表盘联调 | 前端 | | | ⬜ | | | |
| T-F06 | CRM Bug 修复 | 前端 | | | | ⬜ | | |
| T-F07 | CRM 联调验收 | 前端 | | | | ⬜ | | |
| T-F08 | 冒烟测试 | 前端 | | | | | ⬜ | |
| T-F09 | Token 并发锁 | 前端 | | | | | ⬜ | |

---

## 四、联调检查清单

### 后端启动检查

```bash
# 1. 进入后端目录
cd backend

# 2. 安装依赖（如果没装过）
pip install -r requirements.txt
pip install aiosqlite  # Mock 层需要

# 3. 初始化 Mock 数据库
export MOCK_MODE=true
python -c "from app.mock.mock_db import init_mock_db; import asyncio; asyncio.run(init_mock_db())"

# 4. 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 5. 访问 API 文档
# http://localhost:8000/docs
```

### 前端启动检查

```bash
# 1. 进入前端目录
cd frontend-web

# 2. 安装依赖（如果没装过）
npm install

# 3. 确认 .env 配置
# VITE_API_BASE_URL=http://localhost:8000/api/v1

# 4. 启动开发服务器
npm run dev

# 5. 访问前端
# http://localhost:300
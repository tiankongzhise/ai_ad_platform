# Code Review Report — EduAdCRM MVP

> **审查时间**：2026-04-28  
> **审查范围**：`backend/` + `frontend-web/` + `md/` 技术文档  
> **审查方法**：逐文件对比前后端 API 接口、类型定义、数据模型；与技术文档规格进行三方核对  
> **严重级别**：🔴 P0 阻断功能 / 🟠 P1 运行时出错 / 🟡 P2 逻辑隐患 / 🔵 P3 代码质量

---

## 汇总

| 级别 | 数量 | 说明 |
|------|------|------|
| 🔴 P0 | 5 | 功能无法运行，必须修复后才能上线 |
| 🟠 P1 | 6 | 运行时可触发 500/404/类型错误 |
| 🟡 P2 | 7 | 逻辑漏洞、安全隐患、数据不一致 |
| 🔵 P3 | 4 | 代码质量与可维护性建议 |

---

## 🔴 P0 — 阻断性问题（必须在联调前修复）

---

### [P0-1] 后端 90% 路由未注册到 `main.py`

**文件**：`backend/app/main.py`  
**现象**：`main.py` 只注册了 `ad_accounts_router` 一个路由，其余 7 个模块（auth、demo、onboarding、crm、analytics、reports、settings）全部缺失。  
**影响**：前端调用的所有 `authApi`、`demoApi`、`onboardingApi`、`crmApi`、`analyticsApi`、`reportsApi`、`settingsApi` 接口将全部返回 **404**。

```python
# 当前 main.py 只有这一行：
app.include_router(ad_accounts_router, prefix=settings.API_V1_PREFIX)

# 缺少（至少）：
from app.api.v1.auth import router as auth_router
from app.api.v1.demo import router as demo_router
from app.api.v1.onboarding import router as onboarding_router
from app.api.v1.crm import router as crm_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.reports import router as reports_router
from app.api.v1.settings import router as settings_router

app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(demo_router, prefix=settings.API_V1_PREFIX)
# ... 其余路由
```

**根因**：后端 `app/api/v1/` 目录中只存在 `ad_accounts.py` 一个路由文件，其他 7 个路由文件根本未创建。

---

### [P0-2] 后端缺少 7 个路由文件（模块只有骨架无实现）

**文件**：`backend/app/api/v1/`（目录仅含 `__init__.py` 和 `ad_accounts.py`）  
**缺失文件**：

| 文件 | 前端依赖 API | 影响页面 |
|------|------------|---------|
| `auth.py` | `/auth/login`, `/auth/register`, `/auth/refresh`, `/auth/logout`, `/auth/profile` | 登录、注册、全站 Token 刷新 |
| `demo.py` | `/demo/dashboard`, `/demo/metrics` | 演示数据、仪表盘 Demo 模式 |
| `onboarding.py` | `/onboarding/status`, `/onboarding/complete` | 3步引导向导 |
| `crm.py` | `/crm/upload`, `/crm/leads`, `/crm/batches`, ... | CRM 页面所有功能 |
| `analytics.py` | `/analytics/dashboard`, `/analytics/dashboard/status`, `/analytics/trend`, ... | 仪表盘、交叉分析 |
| `reports.py` | `/reports/generate`, `/reports`, `/reports/{id}/download`, `/reports/{id}/insights` | 报表页 |
| `settings.py` | `/settings/tenant`, `/settings/attribution-rules` | 设置页 |

**解决**：根据技术文档第六章接口清单逐一实现。

---

### [P0-3] `TenantContext` 使用类变量实现，存在严重并发安全问题

**文件**：`backend/app/core/tenant.py`  
**问题代码**：
```python
class TenantContext:
    _tenant_id: Optional[str] = None  # ← 类级别变量，所有请求共享！
    _user_id: Optional[str] = None
```
**影响**：FastAPI 基于 `asyncio` 运行，多个并发请求会读写同一个类变量，导致**租户 ID 串行污染**——用户 A 的请求可能拿到用户 B 的 `tenant_id`，造成数据泄露。这是**多租户系统的安全红线**。

**修复方案**：使用 Python 3.7+ 的 `contextvars.ContextVar`：
```python
from contextvars import ContextVar
from typing import Optional

_tenant_id_var: ContextVar[Optional[str]] = ContextVar('tenant_id', default=None)
_user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)

class TenantContext:
    @classmethod
    def set(cls, tenant_id: str, user_id: str) -> None:
        _tenant_id_var.set(tenant_id)
        _user_id_var.set(user_id)

    @classmethod
    def get_tenant_id(cls) -> Optional[str]:
        return _tenant_id_var.get()
```

---

### [P0-4] 后端缺少 `onboarding_status`、`crm_lead`、`crm_import_batch` 等关键 ORM 模型

**文件**：`backend/app/models/`（目录仅含 `user.py`、`tenant.py`、`ad_account.py`、`ad_daily_stat.py`）  
**缺失模型**：

| 缺失文件 | 对应数据库表 | 影响 |
|---------|------------|------|
| `onboarding_status.py` | `onboarding_status` | 引导向导无法持久化 |
| `crm_lead.py` | `crm_leads` | CRM 线索无法存储 |
| `crm_import_batch.py` | `crm_import_batches` | 导入批次无法记录 |
| `attribution_rule.py` | `attribution_rules` | 归因规则无法配置 |
| `report.py` | `reports` | 报表无法生成与存储 |

**影响**：数据库缺少表结构，Alembic 迁移不完整，对应功能模块全部 500。

---

### [P0-5] 后端缺少 `schemas/` 对应文件，前端类型定义大量无对应后端实现

**文件**：`backend/app/schemas/`（仅含 `ad_account.py`）  
**问题**：前端 `types/index.ts` 定义了完整的类型系统，但后端 schemas 目录仅有广告账户一个文件，缺少：
- `auth.py`（`LoginRequest`、`LoginResponse`、`User`）
- `onboarding.py`（`OnboardingStatus`、`OnboardingUpdateRequest`）
- `crm.py`（`ImportProgress`、`FieldMappingResponse`、`CRMLead`、`AttributionSuggestion`）
- `analytics.py`（`DashboardMetrics`、`DashboardStatusResponse`、`CrossTableRow` 等）
- `report.py`（`Report`、`InsightCard`）

---

## 🟠 P1 — 运行时错误（联调必现）

---

### [P1-1] 前端 OAuth 绑定使用 `window.open` 而文档要求 `window.location.href`

**文件**：`frontend-web/src/pages/ad-accounts/index.tsx`（第 76 行）  
**代码**：
```tsx
window.open(oauth_url, '_blank', 'width=600,height=700');
```
**问题**：
1. **`window.open` 弹出的新窗口会被浏览器拦截**（非用户直接点击触发，很多浏览器默认屏蔽）。
2. OAuth 回调 302 重定向到 `FRONTEND_URL/ad-accounts?oauth_result=success`，重定向的是新窗口，**主窗口不会感知到授权结果**，账户列表不会自动刷新。
3. 技术文档 §6A.2 明确要求 `window.location.href = oauth_url`。

**修复**：
```tsx
const { oauth_url } = response.data;
window.location.href = oauth_url;  // 整页跳转，回调后回到当前页并读取 oauth_result
```
同时，`AdAccountsPage` 需要在 `useEffect` 中读取 `location.search` 的 `oauth_result` 参数并展示结果。

---

### [P1-2] `AdAccount.balance` 字段类型不一致（后端 `BigInteger`，前端 `number`，Schema `float`）

**文件**：  
- `backend/app/models/ad_account.py`（第 90-94 行）：`Mapped[Optional[float]]` + `BigInteger`（**类型冲突**）  
- `backend/app/schemas/ad_account.py`（第 32 行）：`Optional[float] = 0`  
- `frontend-web/src/types/index.ts`（第 45 行）：`balance: number`

**问题**：
- ORM 模型中 Python 类型是 `float`，但 SQLAlchemy 列类型是 `BigInteger`——二者不一致，存储小数余额时会被截断。
- 广告账户余额单位通常为分（整数），应使用 `Integer` 或 `Numeric(18,2)`，而非 `BigInteger`。

**修复**：
```python
# 如果单位为"元"，使用 Numeric
balance: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True, default=0)
# 如果单位为"分"，使用 Integer
balance: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
```

---

### [P1-3] `DashboardPage` 解析 `timeRange` 为 `parseInt` 但值是带字母的字符串

**文件**：`frontend-web/src/pages/dashboard/index.tsx`（第 67 行）  
**代码**：
```tsx
analyticsApi.getTrend({ days: parseInt(timeRange) })
```
`timeRange` 的值为 `'7d'`、`'30d'`、`'90d'`（来自 `Segmented` 组件选项），`parseInt('7d')` 确实能返回 `7`，但这是**依赖 `parseInt` 的隐式行为**（截取首部数字），不健壮，且当值为非标准字符串时将返回 `NaN`，导致 API 请求携带 `days=NaN`。

**修复**：选项 value 直接用数字，或在解析时做显式处理：
```tsx
options={[
  { label: '7天', value: 7 },
  { label: '30天', value: 30 },
  { label: '90天', value: 90 },
]}
// 或：
const days = parseInt(timeRange.replace('d', ''), 10);
```

---

### [P1-4] CRM 页面上传弹窗逻辑错误：`beforeUpload` 返回 `false` 导致 `customRequest` 不触发

**文件**：`frontend-web/src/pages/crm/index.tsx`（第 321 行）  
**代码**：
```tsx
<Upload.Dragger
  customRequest={handleUpload}
  beforeUpload={() => false}  // ← 阻止上传，但 customRequest 不会再触发
>
```
`beforeUpload` 返回 `false` 会阻止文件自动上传，**同时也会阻止 `customRequest` 的调用**。二者互斥——设置了 `customRequest` 就不需要 `beforeUpload={() => false}`。

**修复**：删除 `beforeUpload={() => false}` 这一行。

---

### [P1-5] 文档要求 `/crm/upload/{batch_id}/preview` 为 `GET`，但前端调用映射为 `GET`，实际逻辑应触发字段分析（副作用）

**文件**：`frontend-web/src/api/index.ts`（第 137 行）  
**技术文档**：`POST /api/v1/crm/upload/{batch_id}/preview`（文档 §6.2）  
**前端代码**：`axiosInstance.get<FieldMappingResponse>(\`/crm/upload/${batchId}/preview\`)`

**问题**：文档定义为 `POST`，前端实现为 `GET`。这不是小差异——`GET` 不应有副作用，而预览操作需要在服务端触发字段分析（有副作用），应为 `POST`。

**修复**：
```ts
previewMapping: (batchId: string) =>
  axiosInstance.post<FieldMappingResponse>(`/crm/upload/${batchId}/preview`, {}),
```

---

### [P1-6] `AdAccount` 页面在 OAuth 回调后未处理 URL 参数，用户授权结果无反馈

**文件**：`frontend-web/src/pages/ad-accounts/index.tsx`  
**问题**：技术文档 §6A.5 要求前端在 `/ad-accounts` 页面加载时读取 `oauth_result` 并展示 Toast 提醒，但当前实现的 `useEffect` 只调用了 `fetchAccounts()`，完全没有读取 `location.search` 中的回调参数。

**修复**（在 `useEffect` 中添加）：
```tsx
useEffect(() => {
  fetchAccounts();
  // 读取 OAuth 回调结果
  const params = new URLSearchParams(window.location.search);
  const result = params.get('oauth_result');
  const platform = params.get('platform');
  if (result === 'success') {
    message.success(`${platform === 'juliang' ? '巨量引擎' : '百度营销'}账户绑定成功，正在同步数据...`);
  } else if (result === 'cancelled') {
    message.warning('授权已取消');
  } else if (result === 'error') {
    message.error(`绑定失败：${params.get('reason') || '未知错误'}`);
  }
  // 清除 URL 参数，避免刷新重复提示
  if (result) {
    window.history.replaceState({}, '', '/ad-accounts');
  }
}, []);
```

---

## 🟡 P2 — 逻辑隐患与安全问题

---

### [P2-1] `ad_accounts.py` 回调中 `state` 为空时降级为 `default_tenant`，生产环境存在严重安全漏洞

**文件**：`backend/app/api/v1/ad_accounts.py`（第 190-193 行）  
**代码**：
```python
if not tenant_id:
    logger.warning("OAuth 回调未携带有效 state，使用降级租户 ID（仅开发环境）")
    tenant_id = "default_tenant"
```
**问题**：任何人直接访问 `/api/v1/ad/juliang/callback?code=xxx`（不携带 state），都会以 `default_tenant` 身份创建广告账户。这在生产环境是**越权漏洞**。

**修复**：生产环境应直接拒绝无 state 的请求：
```python
if not tenant_id:
    if settings.DEBUG:
        logger.warning("降级到默认租户（仅开发环境）")
        tenant_id = "default_tenant"
    else:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/ad-accounts?oauth_result=error&platform=juliang&reason=missing_state",
            status_code=302,
        )
```

---

### [P2-2] `EmptyState` 组件 scenario 类型与后端返回不一致

**前端定义**（`types/index.ts` 第 210 行）：
```ts
export type DashboardStatus = 'scenario_a' | 'scenario_b' | 'scenario_c' | 'full_data';
```

**前端 `EmptyState` Props 定义**（技术文档 §4.3）：
```ts
interface EmptyStateProps {
  scenario: 'a' | 'b' | 'c';  // ← 不带 "scenario_" 前缀
}
```

**`DashboardPage` 调用**（`dashboard/index.tsx` 第 115 行）：
```tsx
<EmptyState scenario={dashboardStatus} ... />
// dashboardStatus 是 'scenario_a'，但 EmptyState 期望 'a'
```

**影响**：`EmptyState` 组件接收 `'scenario_a'` 但期望 `'a'`，渲染逻辑无法正确判断场景，空态展示失效。

**修复**：统一使用带前缀的格式，两端保持一致：
```tsx
// 方案A：修改 EmptyState props 使用完整格式
scenario: 'scenario_a' | 'scenario_b' | 'scenario_c'

// 方案B：传入时去除前缀
<EmptyState scenario={dashboardStatus?.replace('scenario_', '') as any} />
```

---

### [P2-3] `SyncStatusResponse` 中 `last_sync_at` 类型前后端不一致

**后端 Schema**（`ad_account.py`）：
```python
last_sync_at: Optional[datetime] = None  # Python datetime 对象
```

**前端类型**（`types/index.ts`）：
```ts
last_sync_at?: string;  // ISO string
```

**问题**：后端 FastAPI 序列化 `datetime` 默认输出 ISO 格式字符串，与前端期望 `string` 表面一致，但后端 Redis 存储的 `finished_at` 是手动 `.isoformat()` 的字符串，经过 Pydantic 反序列化时若进行类型校验会失败（字符串 → datetime 转换依赖格式）。

**建议**：显式指定 Pydantic 的序列化格式，或在后端统一使用 ISO 字符串：
```python
class SyncStatusResponse(BaseModel):
    last_sync_at: Optional[str] = None  # 显式 str，与 Redis 数据保持一致
```

---

### [P2-4] `OAuthCallbackResponse` Schema 定义存在但实际回调接口从不返回该格式

**后端 Schema**（`ad_account.py`）：
```python
class OAuthCallbackResponse(BaseModel):
    status: str = "success"
    ad_account_id: str
    account_name: str
    next_step: str = "crm_import"
    message: str = "巨量引擎授权成功"
```

**实际实现**（`ad_accounts.py` OAuth 回调）：返回 `RedirectResponse(302)`，**永远不会返回 JSON**。

**前端代码**（`api/index.ts` 第 101-102 行）：
```ts
juliangCallback: (code: string, state?: string) =>
  axiosInstance.get<OAuthCallbackResponse>('/ad/juliang/callback', { params: { code, state } })
```

**问题**：
1. `OAuthCallbackResponse` Schema 成为死代码，永远不被序列化。
2. 前端手动调用 `juliangCallback` 只会收到 302 重定向响应（Axios 会自动跟随跳转到 HTML 页面），**类型定义 `OAuthCallbackResponse` 完全错误**。
3. 技术文档明确说明回调由广告平台直接 GET，前端不需要手动调用（文档注释已说明"前端处理，不需要手动调用"）。

**建议**：
- 删除前端的 `juliangCallback` 方法（或保留但标注为内部/调试用途）。
- 删除后端 `OAuthCallbackResponse` Schema 或重新定位其用途。

---

### [P2-5] `AdAccount.id` 生成策略使用时间戳，高并发下可能重复

**文件**：`backend/app/models/ad_account.py`（第 43-46 行）  
**代码**：
```python
id: Mapped[str] = mapped_column(
    String(36),
    primary_key=True,
    default=lambda: f"ada_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
)
```
**问题**：`%f` 为微秒（6位），理论上精度足够，但：
1. 并发创建账户时，操作系统时间分辨率不保证微秒唯一。
2. 长度为 `ada_` + 20 字符 = 24 字符，`String(36)` 够用，但风格不一致（UUID 规范是 36 字符含连字符）。
3. 用户模型同样使用此策略（`User.id`）。

**建议**：使用 `uuid.uuid4()` 生成 ID：
```python
import uuid
id: Mapped[str] = mapped_column(
    String(36), primary_key=True, default=lambda: str(uuid.uuid4())
)
```

---

### [P2-6] `CRMPage` 字段映射弹窗逻辑判断反向

**文件**：`frontend-web/src/pages/crm/index.tsx`（第 336 行）  
**代码**：
```tsx
<Modal
  title="确认字段映射"
  open={!!currentBatchId && !attributionModalVisible}  // 归因弹窗打开时，字段映射弹窗才显示？逻辑反了
```
**正确逻辑**：应该是上传完成后先显示字段映射弹窗，确认映射后再显示归因确认弹窗。当前写法导致两个弹窗显示逻辑完全相反。

**上传流程**（`handleUpload`，第 110-115 行）：
```ts
setUploadModalVisible(false);
setAttributionModalVisible(true);  // ← 直接打开了归因弹窗，跳过了字段映射！
```
这说明字段映射（`SmartFieldMapper`）和归因确认（`AttributionConfirm`）的打开顺序混乱：应先字段映射 → 再归因确认。

**建议**：重新梳理弹窗流程：
```
上传成功 → 显示字段映射弹窗 → 确认映射 → 显示归因弹窗 → 确认归因 → 开始导入
```

---

### [P2-7] `DashboardPage` 中 `handleViewDemo` 在渲染函数中调用 Zustand `useStore.getState()`，会导致 React hook 规则违反

**文件**：`frontend-web/src/pages/dashboard/index.tsx`（第 101-103 行）  
**代码**：
```tsx
const handleViewDemo = () => {
  const { enableDemoMode } = useDemoStore.getState();  // ← 在事件处理器中调用 getState()
  enableDemoMode();
};
```
**问题**：在事件处理函数中直接用 `useDemoStore.getState()` 获取 action 是 Zustand 的合法模式，但风格上与其他 store 使用方式不一致（其他地方用 hook destructure）。更重要的是：`DashboardPage` 顶部已经从 `useDemoStore` 解构了 `isDemoMode`、`demoData`、`fetchDemoData`，应该同时解构 `enableDemoMode`：

```tsx
const { isDemoMode, demoData, fetchDemoData, enableDemoMode } = useDemoStore();
// handleViewDemo 直接调用 enableDemoMode()
```

---

## 🔵 P3 — 代码质量建议

---

### [P3-1] 前端 `request.ts` Token 刷新逻辑存在竞态条件

**文件**：`frontend-web/src/api/request.ts`（第 41-56 行）  
**问题**：当多个请求并发触发 401 时，每个请求都会独立发起 Token 刷新，导致 refresh_token 被消耗多次（若后端实现了 refresh_token 单次使用策略，后续刷新会全部失败）。

**建议**：引入刷新锁（promise 复用）：
```ts
let refreshPromise: Promise<string> | null = null;

// 在 401 处理中：
if (!refreshPromise) {
  refreshPromise = axios.post('/api/v1/auth/refresh', { refresh_token: refreshToken })
    .then(res => { refreshPromise = null; return res.data.access_token; })
    .catch(err => { refreshPromise = null; throw err; });
}
const access_token = await refreshPromise;
```

---

### [P3-2] 后端路由缺少统一的 `GlobalExceptionHandler`，自定义异常不会被正确格式化

**文件**：`backend/app/main.py`  
**现状**：只注册了 `global_exception_handler` 捕获通用 `Exception`，但自定义 `EduAdCRMException`（继承自 `HTTPException`）不会进入此 handler。  
**建议**：添加专用 handler：
```python
from app.core.exceptions import EduAdCRMException

@app.exception_handler(EduAdCRMException)
async def edu_exception_handler(request: Request, exc: EduAdCRMException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.detail, "extra": exc.extra},
    )
```

---

### [P3-3] `ad_accounts.py` 回调中 `datetime.now()` 未使用 UTC，Token 过期时间计算存在时区风险

**文件**：`backend/app/api/v1/ad_accounts.py`（第 238、252 行等多处）  
**代码**：`datetime.now() + timedelta(seconds=token_info.expires_in)`  
**问题**：`datetime.now()` 返回本地时间（无时区信息），若服务器时区与数据库时区不一致（常见于容器化部署），Token 过期时间计算会偏差。  
**建议**：统一使用 `datetime.now(timezone.utc)` 或 `datetime.utcnow()`。

---

### [P3-4] `backend/app/models/ad_daily_stat.py` 存在但内容未核实，`ad_accounts.py` 查询中直接导入使用

**文件**：`backend/app/api/v1/ad_accounts.py`（第 636 行）  
**代码**：
```python
from app.models.ad_daily_stat import AdDailyStat
data_query = select(AdDailyStat).where(AdDailyStat.tenant_id == ...)
```
`AdDailyStat` 模型存在于文件系统，但其字段定义需验证是否与技术文档（§5.2）中的 `ad_daily_stats` 表结构一致（特别是 `tenant_id` 字段是否存在）。

---

## 接口对齐矩阵

### 已实现（后端 ↔ 前端均有）

| 接口 | 后端路由 | 前端调用 | 类型对齐 | 状态 |
|------|---------|---------|---------|------|
| `GET /ad/juliang/oauth-url` | ✅ | ✅ | ✅ | 正常 |
| `GET /ad/baidu/oauth-url` | ✅ | ✅ | ✅ | 正常 |
| `GET /ad/juliang/callback` | ✅（302重定向）| ⚠️ 前端误用 | ❌ | 见 P1-1, P2-4 |
| `GET /ad/baidu/callback` | ✅（302重定向）| 未直接调用 | — | 正常 |
| `GET /ad/accounts` | ✅ | ✅ | ✅ | 正常 |
| `GET /ad/accounts/{id}` | ✅ | ✅ | ✅ | 正常 |
| `DELETE /ad/accounts/{id}` | ✅ | ✅ | ✅ | 正常 |
| `POST /ad/accounts/{id}/sync` | ✅ | ✅ | ✅ | 正常 |
| `GET /ad/sync-status` | ✅ | ✅ | ⚠️ | 见 P2-3 |

### 前端有调用，后端路由文件未创建

| 接口 | 对应功能 | 严重性 |
|------|---------|------|
| `POST /auth/login` | 登录 | 🔴 P0 |
| `POST /auth/register` | 注册 | 🔴 P0 |
| `POST /auth/refresh` | Token 刷新 | 🔴 P0 |
| `POST /auth/logout` | 登出 | 🔴 P0 |
| `GET /auth/profile` | 用户信息 | 🔴 P0 |
| `GET /demo/dashboard` | 演示数据 | 🔴 P0 |
| `GET /demo/metrics` | 演示指标 | 🔴 P0 |
| `GET /onboarding/status` | 引导状态 | 🔴 P0 |
| `POST /onboarding/status` | 更新引导 | 🔴 P0 |
| `POST /onboarding/complete` | 完成引导 | 🔴 P0 |
| `POST /crm/upload` | 文件上传 | 🔴 P0 |
| `GET /crm/upload/{task_id}` | 上传进度 | 🔴 P0 |
| `GET /crm/upload/{batch_id}/preview` | 字段预览 | 🔴 P0（含 P1-5 HTTP method 错误）|
| `POST /crm/upload/{batch_id}/confirm` | 确认映射 | 🔴 P0 |
| `GET /crm/upload/{batch_id}/attribution-suggest` | 归因建议 | 🔴 P0 |
| `GET /crm/leads` | 线索列表 | 🔴 P0 |
| `PATCH /crm/leads/{id}` | 更新线索 | 🔴 P0 |
| `DELETE /crm/batches/{id}` | 删除批次 | 🔴 P0 |
| `GET /crm/batches` | 批次列表 | 🔴 P0 |
| `GET /analytics/dashboard` | 仪表盘指标 | 🔴 P0 |
| `GET /analytics/dashboard/status` | 空态判定 | 🔴 P0 |
| `GET /analytics/trend` | 趋势数据 | 🔴 P0 |
| `GET /analytics/channel-compare` | 渠道对比 | 🔴 P0 |
| `GET /analytics/cross-table` | 交叉分析 | 🔴 P0 |
| `GET /analytics/cross-table/export` | 导出 CSV | 🔴 P0 |
| `POST /reports/generate` | 生成报表 | 🔴 P0 |
| `GET /reports` | 报表列表 | 🔴 P0 |
| `GET /reports/{id}/download` | 下载报表 | 🔴 P0 |
| `GET /reports/{id}/insights` | 行动建议 | 🔴 P0 |
| `GET /settings/tenant` | 租户信息 | 🔴 P0 |
| `PATCH /settings/tenant` | 更新租户 | 🔴 P0 |
| `GET /settings/attribution-rules` | 归因规则 | 🔴 P0 |
| `POST /settings/attribution-rules` | 创建规则 | 🔴 P0 |
| `PATCH /settings/attribution-rules/{id}` | 更新规则 | 🔴 P0 |
| `DELETE /settings/attribution-rules/{id}` | 删除规则 | 🔴 P0 |

---

## 修复优先级与建议

### 第一优先级（阻断联调，立即修复）

1. **[P0-1 + P0-2]** 补全后端所有路由文件：`auth.py`、`demo.py`、`onboarding.py`、`crm.py`、`analytics.py`、`reports.py`、`settings.py`，并在 `main.py` 注册。
2. **[P0-3]** 修复 `TenantContext` 使用 `ContextVar`，杜绝并发数据泄露。
3. **[P0-4]** 补全缺失的 ORM 模型文件（至少 `onboarding_status.py`、`crm_lead.py`、`crm_import_batch.py`）。
4. **[P1-1]** 修复 OAuth 绑定使用 `window.location.href` 而非 `window.open`。
5. **[P1-6]** 补全 OAuth 回调结果处理逻辑。

### 第二优先级（功能正确性）

6. **[P2-1]** 生产环境关闭 `state` 为空的降级逻辑。
7. **[P2-2]** 统一 `EmptyState` 的 scenario 类型（前端 `types` 与组件 Props 对齐）。
8. **[P2-6]** 修复 CRM 页面字段映射与归因确认弹窗的显示顺序逻辑。
9. **[P1-2]** 修复 `balance` 字段的 ORM 列类型与 Python 类型不一致问题。
10. **[P1-5]** 修复 `previewMapping` HTTP method 由 GET 改 POST。

### 第三优先级（安全与质量）

11. **[P2-5]** 将 ID 生成策略改为 `uuid.uuid4()`。
12. **[P3-1]** 为 Token 刷新添加并发锁。
13. **[P3-2]** 注册自定义异常 Handler。
14. **[P3-3]** 统一使用 UTC 时间。

---

*本报告由代码审查自动生成 — 2026-04-28*

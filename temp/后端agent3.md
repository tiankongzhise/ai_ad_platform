Now let me analyze the files and compile a comprehensive review report.


发送消息 @general-purpose-3 → 当前 Agent
路由
@general-purpose-3 → 当前 Agent
摘要
Complete code review report for Mock, ORM, Schema files
内容
# 代码审查报告：Mock 层、ORM 模型和 Schema 文件

## 一、文件逐个审查

---

### 1. `backend/app/mock/mock_db.py`

**文件路径**: `C:/Users/3700x/Desktop/ai/ai_ad_platform/backend/app/mock/mock_db.py`

**主要功能描述**:
- 提供 SQLite Mock 数据库连接管理
- 实现异步上下文管理器 `get_mock_db()`
- 初始化 Mock 数据库（执行 schema.sql + 生成演示数据）

**发现的问题**:

| 严重级别 | 问题描述 |
|---------|---------|
| P2 | `MOCK_DB_PATH` 使用相对路径拼接，若从非项目根目录运行可能导致路径错误。建议使用绝对路径或环境变量配置 |
| P3 | 缺少 Mock 数据库连接池配置，高并发场景下可能存在连接问题 |

**与 ORM 模型的一致性检查**: N/A（纯数据库连接层）

---

### 2. `backend/app/mock/seed.py`

**文件路径**: `C:/Users/3700x/Desktop/ai/ai_ad_platform/backend/app/mock/seed.py`

**主要功能描述**:
- 生成"星海教育"演示数据集
- 包含 30 天趋势数据、500 条线索、3 份报表、引导状态、归因规则

**发现的问题**:

| 严重级别 | 问题描述 |
|---------|---------|
| **P0** | **`seed.py` 中缺少租户（Tenant）数据的生成**。所有演示数据都依赖 `demo_tenant_id = "ten_demo_xinghai"`，但 `init_mock_db()` 并未创建对应的 Tenant 记录。若 ORM 查询关联到 Tenant 表将失败 |
| P2 | `_generate_30d_trend` 中使用 `random.uniform` 生成数据，每次运行数据不同，不利于测试稳定性。建议使用固定种子 |
| P3 | 线索生成中 `phone_suffix % 10000` 的掩码逻辑可能导致重复（如 10000000 和 20000000 都映射到 0000） |

**与 Mock Schema 一致性检查**:
- ✅ `mock_dashboard_trend` 字段匹配
- ✅ `mock_crm_leads` 字段匹配
- ✅ `mock_reports` 字段匹配
- ✅ `mock_onboarding` 字段匹配
- ✅ `mock_attribution_rules` 字段匹配

**与 ORM 模型一致性检查**:
- ❌ 缺少对正式 ORM 表（`tenants`、`users`、`ad_accounts` 等）的演示数据生成

---

### 3. `backend/app/models/ad_account.py`

**文件路径**: `C:/Users/3700x/Desktop/ai/ai_ad_platform/backend/app/models/ad_account.py`

**主要功能描述**:
- 广告账户 ORM 模型（巨量引擎/百度营销 OAuth 授权信息）
- 支持 AdPlatform 和 AdAccountStatus 枚举

**发现的问题**:

| 严重级别 | 问题描述 |
|---------|---------|
| **P1** | **`balance` 字段类型不匹配**：`BigInteger` 用于存储余额，但注释说"实际存储单位：分"，这意味着应该是整数。但 Pydantic Schema 中定义为 `float`。如果 ORM 和 Schema 类型不一致会导致数据转换问题 |
| P2 | 缺少对 `account_id` 的唯一性约束。同一平台下的 `account_id` 应该全局唯一或在同一租户内唯一 |
| P3 | 注释掉的关联关系（`tenant`、`daily_stats`）应该保留或删除，避免代码混淆 |
| P3 | `id` 默认值使用时间戳生成，高并发下存在 ID 碰撞风险（微秒级别） |

**与前端类型定义一致性检查**:
- ✅ `AdPlatform` 类型匹配（`'juliang' | 'baidu'`）
- ✅ `AdAccountStatus` 类型匹配
- ✅ 主要字段存在性一致

---

### 4. `backend/app/models/ad_daily_stat.py`

**文件路径**: `C:/Users/3700x/Desktop/ai/ai_ad_platform/backend/app/models/ad_daily_stat.py`

**主要功能描述**:
- 广告每日数据统计 ORM 模型
- 包含计划/单元层级数据、核心指标、计算指标

**发现的问题**:

| 严重级别 | 问题描述 |
|---------|---------|
| **P0** | **字段类型严重不一致**：`spend`、`impressions`、`clicks`、`form_submissions` 等核心指标字段使用 `BigInteger` 类型，但实际业务中：<br>1. `spend`（花费）应以"分"为单位存储为整数 → BigInteger 合理<br>2. `impressions`、`clicks`、`form_submissions` 是计数，应为整数 → BigInteger 合理<br>3. `cost_per_click`、`cost_per_form` 是比率/单价，应为浮点数，但定义为 `BigInteger` → **类型错误** |
| **P0** | **`stat_date` 字段类型问题**：定义为 `Date` 类型但实际是 `datetime` 对象，可能导致时区问题 |
| P1 | 缺少对 `spend` 的非负约束和范围检查 |
| P2 | 缺少对 `campaign_id` 的唯一性约束（同一账户、同一日期、同一计划） |

**与前端类型定义一致性检查**:
- ✅ `DemoTrendData` 接口与字段名匹配
- ✅ `ChannelComparison` 接口与字段名匹配

---

### 5. `backend/app/models/user.py`

**文件路径**: `C:/Users/3700x/Desktop/ai/ai_ad_platform/backend/app/models/user.py`

**主要功能描述**:
- 用户 ORM 模型
- 包含邮箱/密码认证、角色、个人资料

**发现的问题**:

| 严重级别 | 问题描述 |
|---------|---------|
| P2 | 缺少对 `email` 的唯一性约束在同一租户内的检查（当前是全局唯一，可能不符合多租户场景） |
| P3 | `password_hash` 字段长度限制为 255，但 bcrypt 哈希结果可能超过此长度（取决于实现） |

**与前端类型定义一致性检查**:
- ✅ `User` 接口字段基本匹配
- ❌ 前端 `User.is_active` 为 boolean，后端 ORM 有 `is_active` → 一致
- ⚠️ 前端 `User` 缺少 `updated_at`、`last_login_at`、`phone`、`email_verified`、`wx_openid` 字段，但这些字段可能不需要暴露给前端

---

### 6. `backend/app/models/tenant.py`

**文件路径**: `C:/Users/3700x/Desktop/ai/ai_ad_platform/backend/app/models/tenant.py`

**主要功能描述**:
- 租户 ORM 模型
- 包含租户名称、行业、产品/课程配置

**发现的问题**:

| 严重级别 | 问题描述 |
|---------|---------|
| **P0** | **缺少唯一性约束**：没有对 `name` 字段添加唯一性约束，可能导致同名租户冲突 |
| P2 | 缺少对 `settings` JSON 字段的结构验证 |
| P3 | 缺少业务状态字段（如 `is_trial`、`trial_expires_at`）的演示功能支持 |

**与前端类型定义一致性检查**:
- ⚠️ 前端 `OnboardingStep1` 包含 `name`、`industry_sub_type`、`main_product`，与 Tenant 模型字段对应
- ✅ 租户相关类型匹配

---

### 7. `backend/app/schemas/ad_account.py`

**文件路径**: `C:/Users/3700x/Desktop/ai/ai_ad_platform/backend/app/schemas/ad_account.py`

**主要功能描述**:
- 广告账户 Pydantic Schema
- 提供创建、更新、响应等数据验证

**发现的问题**:

| 严重级别 | 问题描述 |
|---------|---------|
| **P1** | **Schema 字段验证不完整**：<br>1. `platform` 字段无枚举限制，应验证为 `juliang` 或 `baidu`<br>2. `status` 字段无枚举限制 |
| P2 | `AdAccountBase` 缺少 `tenant_id` 字段，但在创建时需要 |
| P3 | `OAuthCallbackResponse.next_step` 应为枚举或有限字符串集合 |

**与 ORM 模型一致性检查**:
- ✅ `AdAccountResponse` 与 `AdAccount` ORM 模型字段基本匹配
- ⚠️ `balance` 类型：ORM 用 BigInteger，Schema 用 float → 存在不一致

---

### 8. `backend/app/schemas/auth.py`

**文件路径**: `C:/Users/3700x/Desktop/ai/ai_ad_platform/backend/app/schemas/auth.py`

**主要功能描述**:
- 认证相关 Pydantic Schema
- 提供注册、登录、Token 刷新等数据验证

**发现的问题**:

| 严重级别 | 问题描述 |
|---------|---------|
| P2 | `RegisterRequest.org_name` 对应 ORM `Tenant.name`，但命名不一致 |
| P3 | `LoginResponse` 和 `RegisterResponse` 缺少 `expires_in` 字段，而前端 `LoginResponse` 需要此字段 |

**与 ORM 模型一致性检查**:
- ✅ `UserResponse` 与 `User` ORM 模型主要字段匹配
- ⚠️ `UserResponse` 缺少 `updated_at`、`last_login_at`、`is_active`、`email_verified`、`phone` 字段

**与前端类型定义一致性检查**:
- ❌ **关键不一致**：`LoginResponse` 后端无 `expires_in` 字段，前端有 `expires_in: number` 需求

---

### 9. `frontend-web/src/types/index.ts`

**文件路径**: `C:/Users/3700x/Desktop/ai/ai_ad_platform/frontend-web/src/types/index.ts`

**主要功能描述**:
- 前端 TypeScript 类型定义
- 与后端 Pydantic Schema 对应

**发现的问题**:

| 严重级别 | 问题描述 |
|---------|---------|
| P2 | `User` 接口缺少 `updated_at`、`last_login_at`、`email_verified`、`wx_openid` 字段，可能导致显示不完整 |
| P3 | `RegisterRequest.tenant_name` 与后端 `RegisterRequest.org_name` 命名不一致 |

---

### 10. `backend/app/mock/schema.sql`

**文件路径**: `C:/Users/3700x/Desktop/ai/ai_ad_platform/backend/app/mock/schema.sql`

**主要功能描述**:
- SQLite Mock 数据库表结构定义
- 包含 7 张演示数据表

**发现的问题**:

| 严重级别 | 问题描述 |
|---------|---------|
| **P0** | **Mock Schema 与 ORM Schema 完全不同**：<br>1. Mock 表都以 `mock_` 前缀命名<br>2. Mock 表结构（字段、类型）与 ORM 模型无对应关系<br>3. Mock 表缺少 ORM 模型中的核心表（`tenants`、`users`、`ad_accounts`、`ad_daily_stats`）的对应表 |
| **P1** | **`mock_crm_leads`** 表缺少 `batch_id` 外键约束关联到 `mock_crm_batches` |
| P2 | `mock_dashboard_trend.platform` 应添加 CHECK 约束限制为 `('juliang', 'baidu', 'combined')` |
| P3 | `mock_reports.date_range_start` 和 `date_range_end` 缺少 CHECK 约束确保 end >= start |

**与 ORM Schema 一致性检查**:
- ❌ Mock 数据库是独立的数据集，与正式 ORM 表无直接对应关系
- ❌ 建议：Mock 层应同时包含对正式表的种子数据，以便切换时数据连续

---

## 二、整体评估

### 整体评分：6.5 / 10

### 关键发现汇总

#### 🔴 严重问题（P0）

1. **Mock 数据层缺少 Tenant 数据生成**
   - 所有演示数据依赖 `ten_demo_xinghai` 租户 ID，但未创建对应 Tenant 记录
   - 影响：任何涉及租户关联的 ORM 查询将失败

2. **ORM 字段类型与业务语义不匹配（ad_daily_stat.py）**
   - `cost_per_click`、`cost_per_form` 定义为 BigInteger，但应为浮点数
   - 影响：数值计算精度丢失

3. **Mock 数据库与 ORM 模型完全隔离**
   - Mock 表（`mock_*`）与 ORM 表（`ad_accounts`、`users` 等）无对应关系
   - 影响：无法进行端到端 Mock 测试

4. **Tenant 模型缺少 name 唯一性约束**
   - 可能导致同名租户冲突

#### 🟠 中等问题（P1）

1. **前后端类型不一致**
   - `LoginResponse` 后端缺少 `expires_in` 字段
   - `RegisterRequest` 字段命名不一致（`org_name` vs `tenant_name`）

2. **Pydantic Schema 缺少枚举验证**
   - `platform`、`status` 等字段无枚举限制

3. **balance 字段类型不一致**
   - ORM 用 BigInteger，Schema 用 float

#### 🟡 轻微问题（P2/P3）

1. Mock 数据随机生成，每次运行结果不同
2. ID 生成使用时间戳，高并发下存在碰撞风险
3. 缺少 JSON 字段结构验证
4. 注释掉的关联关系应清理

---

## 三、修复建议优先级

### 高优先级（必须修复）

1. 在 `seed.py` 中添加 Tenant 和 User 演示数据生成
2. 修复 `ad_daily_stat.py` 中 `cost_per_click`、`cost_per_form` 的字段类型为 Float
3. 为 `Tenant.name` 添加唯一性约束
4. 统一前后端类型定义（`expires_in`、`tenant_name`）

### 中优先级（建议修复）

1. 在 Pydantic Schema 中添加字段枚举验证
2. Mock 层增加对正式 ORM 表的种子数据支持
3. 统一 `balance` 字段类型定义

### 低优先级（可选优化）

1. 使用固定随机种子确保 Mock 数据可重现
2. 清理注释代码
3. 添加 ID 生成器替代时间戳

---

报告生成时间：2026-04-28
审查范围：Mock 层、ORM 模型、Schema 定义、前后端类型一致性
结果
消息已发送给 当前 Agent。
代码审查报告已生成并发送给 team-lead。

##审查摘要

共审查 10 个文件：

2 个 Mock 层文件（mock_db.py、seed.py、schema.sql）
4 个 ORM 模型文件（ad_account、ad_daily_stat、user、tenant）
2 个 Pydantic Schema 文件（ad_account、auth） -1 个前端类型定义文件（index.ts）
发现的关键问题
P0 严重问题（4个）:

seed.py 缺少 Tenant 数据生成，导致演示数据无法关联租户
ad_daily_stat.py 中 cost_per_click、cost_per_form 类型错误（BigInteger 应为 Float）
Mock 数据库与 ORM 模型完全隔离，无法进行端到端测试
Tenant.name 缺少唯一性约束
P1 中等问题（3个）:

LoginResponse 缺少 expires_in 字段
platform、status 等字段无枚举验证
balance 字段类型不一致
整体评分：6.5 / 10 I've completed the code review task. Let me provide a summary of what I did.

代码审查报告已生成并发送给 team-lead。

审查摘要
共审查 10 个文件：

2 个 Mock 层文件（mock_db.py、seed.py、schema.sql）
4 个 ORM 模型文件（ad_account、ad_daily_stat、user、tenant）
2 个 Pydantic Schema 文件（ad_account、auth）
1 个前端类型定义文件（index.ts）
发现的关键问题
P0 严重问题（4个）:

seed.py 缺少 Tenant 数据生成，导致演示数据无法关联租户
ad_daily_stat.py 中 cost_per_click、cost_per_form 类型错误（BigInteger 应为 Float）
Mock 数据库与 ORM 模型完全隔离，无法进行端到端测试
Tenant.name 缺少唯一性约束
P1 中等问题（3个）:

LoginResponse 缺少 expires_in 字段
platform、status 等字段无枚举验证
balance 字段类型不一致
整体评分：6.5 / 10
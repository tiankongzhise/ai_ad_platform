# 后端 Bug 修复清单

> **基于**: 第一阶段迅敏开发代码审核意见 (CODE_REVIEW.md)
> **负责人**: 后端开发负责人
> **创建时间**: 2026-04-28
> **完成时间**: 2026-04-28
> **状态说明**: [ ] 待修复 | [x] 已修复

---

## 🔴 P0 — 阻断性问题

| 编号 | Bug 名称 | 严重级别 | 状态 | 修复说明 |
|------|---------|---------|------|---------|
| BUG-01 | 路由未注册到 main.py | 🔴 P0 | [x] | ✅ 经验证，main.py 已注册全部 8 个路由，审核意见基于旧版代码 |
| BUG-02 | 缺少 7 个路由文件 | 🔴 P0 | [x] | ✅ 经验证，7 个路由文件已存在，但端点不完整（见 BUG-11~14 补充） |
| BUG-03 | TenantContext 并发安全问题 | 🔴 P0 | [x] | ✅ ContextVar 已使用，新增 TenantContextCleanupMiddleware 防止上下文泄漏 |
| BUG-04 | 缺少 ORM 模型文件 | 🔴 P0 | [x] | ✅ 新增 onboarding_status/crm_lead/crm_import_batch/attribution_rule/report 五个模型 |
| BUG-05 | 缺少 Schemas 文件 | 🔴 P0 | [x] | ✅ 新增 onboarding/crm/analytics/report 四个 Schema 文件 |

## 🟠 P1 — 运行时错误

| 编号 | Bug 名称 | 严重级别 | 状态 | 修复说明 |
|------|---------|---------|------|---------|
| BUG-06 | AdAccount.balance 字段类型不一致 | 🟠 P1 | [x] | ✅ BigInteger→Numeric(18,2)；AdDailyStat.spend→Integer，计算指标→Numeric |
| BUG-07 | SyncStatusResponse.last_sync_at 类型不一致 | 🟡 P2 | [x] | ✅ datetime→str，与 Redis 存储保持一致 |
| BUG-08 | OAuthCallbackResponse Schema 死代码 | 🟡 P2 | [x] | ✅ 删除死代码 Schema 和路由 import |
| BUG-11 | CRM 缺少 preview/confirm 端点 | 🟠 P1 | [x] | ✅ 新增 POST preview + POST confirm 端点 |
| BUG-12 | CRM 缺少 attribution-suggest 端点 | 🟠 P1 | [x] | ✅ 新增 GET attribution-suggest 端点 |
| BUG-13 | CRM 缺少 PATCH leads/{id} 端点 | 🟠 P1 | [x] | ✅ 新增 PATCH leads/{id} 端点 |
| BUG-14 | Analytics 缺少 cross-table 端点 | 🟠 P1 | [x] | ✅ 新增 GET cross-table + GET cross-table/export 端点 |

## 🟡 P2 — 逻辑隐患与安全问题

| 编号 | Bug 名称 | 严重级别 | 状态 | 修复说明 |
|------|---------|---------|------|---------|
| BUG-09 | OAuth 回调 state 为空时降级为 default_tenant | 🟡 P2 | [x] | ✅ 巨量引擎回调增加 settings.DEBUG 判断，生产环境拒绝无 state 请求 |
| BUG-10 | ID 生成策略使用时间戳，高并发可能重复 | 🟡 P2 | [x] | ✅ 四个模型统一改为 uuid.uuid4() |

## 🔵 P3 — 代码质量

| 编号 | Bug 名称 | 严重级别 | 状态 | 修复说明 |
|------|---------|---------|------|---------|
| BUG-15 | 缺少 EduAdCRMException 专用异常处理器 | 🔵 P3 | [x] | ✅ main.py 注册 EduAdCRMException handler，输出 code/extra 字段 |
| BUG-16 | ad_accounts.py datetime.now() 未使用 UTC | 🔵 P3 | [x] | ✅ 所有 datetime.now() 改为 datetime.now(timezone.utc) |
| BUG-17 | models/__init__.py 未导出所有模型 | 🔵 P3 | [x] | ✅ 导入全部模型和枚举，支持 Alembic 自动发现 |
| BUG-18 | CRM 上传文件路径硬编码 /tmp | 🔵 P3 | [x] | ✅ 改为 settings.LOCAL_STORAGE_PATH + /crm_uploads |

---

## 修复统计

| 级别 | 总数 | 已修复 | 跳过（验证后无需修复） |
|------|------|--------|---------------------|
| 🔴 P0 | 5 | 3 | 2（BUG-01/02 已存在） |
| 🟠 P1 | 7 | 7 | 0 |
| 🟡 P2 | 2 | 2 | 0 |
| 🔵 P3 | 4 | 4 | 0 |
| **合计** | **18** | **16** | **2** |

---

*本清单由后端开发负责人根据代码审核意见整理 — 2026-04-28*
*全部后端 Bug 修复完成 — 2026-04-28*

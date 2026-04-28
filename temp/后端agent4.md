mprehensive code review report and send it to the team lead.


发送消息 @general-purpose-4 → 当前 Agent
路由
@general-purpose-4 → 当前 Agent
摘要
Complete frontend code review report for all 27 files
内容
# 前端代码审查报告（完整版）

## 一、API 层

### 1. `frontend-web/src/api/request.ts`
**主要功能**: Axios 实例封装，统一处理 Token 注入、401 刷新、错误提示。

**已修复问题确认**:
- ✅ **P3-1 Token刷新竞态**: 已使用 `refreshPromise` Promise 锁机制，避免并发刷新。`finally` 块中清除锁。
- ✅ **P1-1 OAuth跳转**: Token 刷新使用 `window.location.href = '/login'` 整页跳转而非弹窗。

**发现的问题**:
- **P2 逻辑隐患 (request.ts:13)**: `baseURL` 硬编码为 `/api/v1`，但 Token 刷新请求（第51行）也直接使用 `axios.post('/api/v1/auth/refresh')` 而非 `axiosInstance`。如果 `VITE_API_BASE_URL` 配置了非默认值，刷新请求的 URL 不会随之变化。应抽取 baseURL 为常量或使用 `axiosInstance` 做刷新（注意避免循环触发拦截器）。
- **P2 逻辑隐患 (request.ts:63)**: Token 刷新失败时 `throw refreshError` 后又会被 `catch` 块（第78行）捕获，最终执行 `Promise.reject(error)` 返回原始的请求错误而非刷新错误。用户收到的错误信息可能不准确。
- **P3 代码质量 (request.ts:87-93)**: 非401错误直接调用 `message.error` 展示全局 Toast，但没有区分网络超时 vs 4xx vs 5xx 的细微差别。网络断开时 `error.response` 为 `undefined`，此时不会有任何提示。

**代码质量评价**: 7/10 — Token 刷新机制设计合理，但硬编码 baseURL 和错误处理细节需打磨。

---

### 2. `frontend-web/src/api/index.ts`
**主要功能**: 封装所有后端 API 调用，与后端 FastAPI 路由一一对应。

**已修复问题确认**:
- ✅ **P1-5 previewMapping HTTP方法**: 现在使用 `axiosInstance.get`（GET 请求），正确。

**发现的问题**:
- **P2 逻辑隐患 (index.ts:144)**: `getAttributionSuggest` 路径为 `/crm/upload/${batchId}/attribution-suggest`，是 GET 方法。如果 batch 数据量大，可能超出 URL 长度限制，但当前场景合理。
- **P3 代码质量 (index.ts:219,227)**: `settingsApi.getTenant` 和 `settingsApi.getAttributionRules` 没有声明返回类型参数，TypeScript 无法推断响应体结构，丢失了类型安全。
- **P3 代码质量**: `crmApi.upload` 的 `onUploadProgress` 回调定义在参数中，如果后续需要复用上传逻辑，可以提取为独立函数。不过当前内联也是合理的。

**代码质量评价**: 8/10 — 结构清晰、模块化好。少数 API 缺少返回类型注解。

---

## 二、Store 层

### 3. `frontend-web/src/store/authStore.ts`
**主要功能**: 认证状态管理（登录、注册、登出、Token 持久化）。

**已修复问题确认**:
- ✅ **P2-7 getState**: login 的 register 方法已使用 `get().login()` 而非直接调用，正确。

**发现的问题**:
- **P2 逻辑隐患 (authStore.ts:39-40)**: `login` 方法同时写 `localStorage` 和 `zustand persist`（第122-128行）。Token 存在两个地方：localStorage 和 zustand 的 `auth-storage`。如果用户通过浏览器开发者工具清除了 localStorage，zustand 中仍有旧 token；反之亦然。可能导致状态不一致。
- **P2 逻辑隐患 (authStore.ts:87-114)**: `checkAuth` 方法每次被多个 `ProtectedRoute`/`PublicRoute` 同时调用时（App.tsx 第27行和第58行），没有去重机制，可能并发触发多次 `getProfile` 请求。
- **P3 代码质量 (authStore.ts:104)**: `checkAuth` catch 块中清除 token 但没有通知用户（比如跳转登录页），仅静默重置状态。如果用户 token 过期但仍在受保护路由，会看到空白页面（`return null` 在 App.tsx:47）。

**代码质量评价**: 7/10 — 核心逻辑正确，但 Token 双写和 checkAuth 去重需关注。

---

### 4. `frontend-web/src/store/demoStore.ts`
**主要功能**: 演示模式控制与数据缓存。

**发现的问题**:
- **P3 代码质量 (demoStore.ts:57-71)**: `fetchDemoData` catch 中只设 `error` 状态但不 throw，调用方无法知道请求失败。
- **P3 代码质量**: persist 配置中缓存了 `demoData`，对于大型演示数据集可能浪费 localStorage 空间，但对当前场景影响不大。

**代码质量评价**: 8/10 — 简洁实用。

---

### 5. `frontend-web/src/store/onboardingStore.ts`
**主要功能**: 引导流程状态管理（3步进度追踪）。

**发现的问题**:
- **P3 代码质量 (onboardingStore.ts:44-48)**: `completed_at` 和 `step2_ad_bound` 两种情况下 `currentStep` 都设为 3，逻辑正确但可读性可提升，加个注释说明。
- **P3 代码质量 (onboardingStore.ts:61)**: `(error as any).response?.status === 404` — 使用 `as any` 绕过类型检查。可以从 axios error 中提取 AxiosError 类型。

**代码质量评价**: 8/10 — 逻辑清晰，步骤计算正确。

---

## 三、页面组件

### 6. `frontend-web/src/pages/login/index.tsx`
**主要功能**: 登录/注册页面，Tab 切换。

**发现的问题**:
- **P3 代码质量 (login/index.tsx:22,33)**: `catch (err: any)` 使用 any 类型。可使用 `AxiosError` 进行类型收窄。
- **P3 代码质量**: 注册表单缺少"确认密码"字段。用户体验可以改进，但不是 bug。

**代码质量评价**: 8/10 — 功能完整，表单验证到位。

---

### 7. `frontend-web/src/pages/ad-accounts/index.tsx`
**主要功能**: 广告账户管理，OAuth 绑定，手动同步。

**已修复问题确认**:
- ✅ **P1-1 OAuth跳转**: 使用 `window.location.href = oauth_url` 整页跳转，不会被弹窗拦截器拦截。
- ✅ **P1-6 OAuth回调**: 使用 URL 参数 `oauth_result` 处理回调，`replaceState` 清除 URL 参数。

**发现的问题**:
- **P2 逻辑隐患 (ad-accounts/index.tsx:60-84)**: `useEffect` 依赖数组为空 `[]`，但内部调用了 `fetchAccounts()`。由于 ESLint exhaustive-deps 规则，`fetchAccounts` 应该在依赖数组中，否则可能导致闭包陈旧问题。
- **P3 代码质量 (ad-accounts/index.tsx:119)**: `manualSync` 中 `days: 7` 是硬编码的，应考虑允许用户选择同步天数。

**代码质量评价**: 7/10 — OAuth 流程处理得当，但 useEffect 依赖需修正。

---

### 8. `frontend-web/src/pages/dashboard/index.tsx`
**主要功能**: 仪表盘核心指标展示，支持真实数据和演示数据切换。

**已修复问题确认**:
- ✅ **P2-2 EmptyState scenario**: 传入 `DashboardStatus` 类型的 `scenario` 属性给 `EmptyState`。
- ✅ **P2-7 getState**: 第101行使用 `useDemoStore.getState().enableDemoMode()`。

**发现的问题**:
- **P2 逻辑隐患 (dashboard/index.tsx:130)**: `platform: c.platform as any` — 将 `string` 强转为 `AdPlatform` 类型。如果后端演示数据中 platform 值不在 `'juliang' | 'baidu'` 范围内，会导致运行时问题。
- **P2 逻辑隐患 (dashboard/index.tsx:80-83)**: `handleTimeRangeChange` 更新 `timeRange` 但不会触发 `fetchData()`，需要用户手动刷新。`dateRange` 更新了但也没有被实际使用（`fetchData` 中用的是 `timeRange`）。RangePicker 的 `onChange`（第168行）也没有触发数据刷新。
- **P3 代码质量 (dashboard/index.tsx:42-47)**: `useEffect` 依赖数组缺少 `fetchStatus` 和 `fetchData`，可能触发 ESLint 警告。
- **P3 代码质量 (dashboard/index.tsx:117)**: `onSkip={() => {}}` 空回调，可读性不佳。

**代码质量评价**: 6/10 — 空态处理和演示模式切换设计好，但时间范围切换不触发刷新是明显的功能缺陷。

---

### 9. `frontend-web/src/pages/crm/index.tsx`
**主要功能**: CRM 线索管理，Excel 导入，字段映射，归因确认。

**已修复问题确认**:
- ✅ **P1-3 parseInt**: 未发现 parseInt 使用，使用的是 dayjs。
- ✅ **P2-6 CRM弹窗顺序**: 上传成功后先关闭 uploadModal，再打开 attributionModal（第113-115行）。

**发现的问题**:
- **P2 逻辑隐患 (crm/index.tsx:124-135)**: `handleMappingConfirm` 在 CRM 页面中直接调用 `crmApi.confirmMapping`，但归因确认弹窗（AttributionConfirm）的 `onConfirm` 也调用 `handleMappingConfirm`。归因规则数据（`selectedRules`）实际上是传给 `confirmMapping` 的 `mappings`，但 `confirmMapping` API 期望的是 `field_mappings: Record<string, string>`（字段映射），而非归因规则。**这可能是 API 语义混淆：归因规则和字段映射是两个不同的概念。**
- **P2 逻辑隐患 (crm/index.tsx:146)**: `deal_status: status as any` — 缺少类型守卫，应该验证 status 值是否在合法范围内。
- **P3 代码质量 (crm/index.tsx:94-97)**: `useEffect` 依赖数组包含 `filters` 对象引用，每次渲染 filters 都是新对象，可能导致无限循环。应使用具体的 `filters.deal_status` 作为依赖。
- **P3 代码质量 (crm/index.tsx:251)**: 搜索按钮没有绑定 onClick 事件处理函数。

**代码质量评价**: 6/10 — 功能复杂度较高，弹窗流程管理得当，但字段映射与归因确认的数据流混淆，filters 依赖可能导致性能问题。

---

### 10. `frontend-web/src/pages/onboarding/index.tsx`
**主要功能**: 3步引导配置独立页面。

**发现的问题**:
- **P3 代码质量 (onboarding/index.tsx:13)**: `const step = searchParams.get('step')` 获取了 `step` 参数但从未使用。
- **P3 代码质量**: 页面结构简单清晰，无重大问题。

**代码质量评价**: 9/10 — 简洁明了。

---

### 11. `frontend-web/src/pages/reports/index.tsx`
**主要功能**: 报表生成、下载、查看行动建议。

**发现的问题**:
- **P2 逻辑隐患 (reports/index.tsx:92)**: 下载文件扩展名判断 `report.report_type.includes('excel')` — 但 `REPORT_TYPE_OPTIONS` 中没有包含 'excel' 的选项（只有 'daily_roi', 'weekly_roi', 'monthly_roi', 'channel_analysis'），所以永远返回 'pdf'。
- **P3 代码质量 (reports/index.tsx:106)**: `setIsLoading(true)` 和 `setInsightModalVisible(true)` 在查看行动建议时同时设置，loading 状态是全局的，与报表列表的 loading 共用 `isLoading` 变量。查看建议时不应该让整个页面显示 loading。

**代码质量评价**: 7/10 — 功能完整，但文件扩展名判断逻辑和 loading 状态共用是问题。

---

### 12. `frontend-web/src/pages/settings/index.tsx`
**主要功能**: 归因规则管理和账户设置。

**发现的问题**:
- **P2 逻辑隐患 (settings/index.tsx:203-216)**: "账户设置" Tab 中的表单（机构名称、行业细分、主营课程）是纯静态的，没有与后端 API 联动。Input 组件没有绑定 `value`，保存按钮的 `onClick` 没有处理函数。这个功能是未完成的。
- **P3 代码质量 (settings/index.tsx:244-252)**: 使用原生 `<select>` 而非 Ant Design 的 `<Select>` 组件，与项目整体风格不一致，且不受 Form 的控制。

**代码质量评价**: 6/10 — 归因规则 CRUD 正常，但账户设置功能完全未实现。

---

### 13. `frontend-web/src/pages/analytics/index.tsx`
**主要功能**: 交叉分析，广告计划与课程数据表格 + ECharts 图表。

**发现的问题**:
- **P2 逻辑隐患 (analytics/index.tsx:211-213)**: `RangePicker` 更新 `dateRange` 但没有触发 `fetchData()`，日期筛选无效。
- **P3 代码质量 (analytics/index.tsx:143-200)**: `chartOption` 定义在组件内但在渲染时创建（未使用 useMemo），每次渲染都会创建新对象，可能导致 ECharts 重新初始化。
- **P3 代码质量**: 整体结构清晰，ECharts 集成合理。

**代码质量评价**: 7/10 — 图表展示效果好，但日期筛选未联动数据请求。

---

## 四、Hooks

### 14. `frontend-web/src/hooks/useDashboardStatus.ts`
**主要功能**: 获取仪表盘状态，决定空态场景。

**发现的问题**:
- **P3 代码质量**: 实现简洁规范。无重大问题。

**代码质量评价**: 9/10 — 清晰的 hook 封装。

---

### 15. `frontend-web/src/hooks/useImportProgress.ts`
**主要功能**: 轮询导入任务进度。

**发现的问题**:
- **P2 逻辑隐患 (useImportProgress.ts:84)**: `fetchProgress` 的 `useCallback` 依赖了 `maxAttempts, onComplete, onError, stopPolling`。如果调用方没有用 `useCallback` 包裹 `onComplete`/`onError`，会导致 `fetchProgress` 频繁重建，进而导致 `startPolling` 也重建。
- **P3 代码质量 (useImportProgress.ts:61)**: `setIsLoading(false)` 只在第一次成功获取后设置，如果网络持续失败，`isLoading` 会一直为 true。

**代码质量评价**: 7/10 — 轮询机制设计合理，但依赖链需注意。

---

### 16. `frontend-web/src/hooks/usePolling.ts`
**主要功能**: 通用轮询 Hook。

**发现的问题**:
- **P2 逻辑隐患 (usePolling.ts:79-96)**: `useEffect` 的依赖数组包含 `fetchData`，而 `fetchData` 依赖 `maxAttempts`。如果 `options.maxAttempts` 每次渲染都是新值（非 memoized），会导致轮询重启。建议在 hook 内部使用 ref 存储 options。
- **P3 代码质量 (usePolling.ts:55-71)**: `fetchData` 中没有设置 `isLoading`，只有 `refetch` 设置了。轮询获取数据时用户无法看到 loading 状态。

**代码质量评价**: 7/10 — 通用设计好，但依赖稳定性需加强。

---

## 五、组件层

### 17. `frontend-web/src/components/EmptyState/index.tsx`
**主要功能**: 分场景空态引导组件。

**已修复问题确认**:
- ✅ **P2-2 EmptyState scenario**: `scenario` 属性类型为 `DashboardStatus`，SCENARIOS Record 覆盖了所有 4 种状态。

**发现的问题**:
- **P3 代码质量 (EmptyState/index.tsx:36,51)**: `secondaryAction.onClick` 定义为 `() => {}` 空函数，实际调用时由 `onViewDemo` prop 处理。如果 `onViewDemo` 为 undefined，点击按钮无反应，没有反馈。
- **P3 代码质量**: 组件设计合理，场景配置清晰。

**代码质量评价**: 8/10 — 场景化设计好。

---

### 18. `frontend-web/src/components/OnboardingWizard/index.tsx`
**主要功能**: 3步引导向导弹窗组件。

**已修复问题确认**:
- ✅ **P1-4 beforeUpload**: 未使用 beforeUpload，CRM 页面的上传使用 customRequest。

**发现的问题**:
- **P2 逻辑隐患 (OnboardingWizard/index.tsx:72)**: OAuth 授权使用 `window.open(oauth_url, '_blank', 'width=600,height=700')` 弹窗方式。**这与 ad-accounts 页面使用的 `window.location.href`（整页跳转）不一致。** 弹窗方式可能被浏览器拦截，且回调处理在弹窗中可能不生效。**但注意：** 在向导上下文中弹窗更合适，因为用户不想离开当前页面。需要确保 OAuth 回调页面能正确处理弹窗场景（如使用 `window.opener.postMessage`）。
- **P3 代码质量 (OnboardingWizard/index.tsx:85)**: `selectedPlatforms as any` — 类型断言绕过检查。
- **P3 代码质量 (OnboardingWizard/index.tsx:256)**: Step 3 使用 `window.location.href = '/crm'` 而非 React Router 的 `navigate('/crm')`，会导致整个应用重新加载。

**代码质量评价**: 7/10 — 向导交互设计好，但 OAuth 弹窗 vs 整页跳转不一致。

---

### 19. `frontend-web/src/components/SmartFieldMapper/index.tsx`
**主要功能**: 智能字段映射组件，Excel 列名到标准字段的匹配确认。

**发现的问题**:
- **P3 代码质量 (SmartFieldMapper/index.tsx:68-69)**: `handleConfirm` 中检查了必填字段缺失但没有给用户任何提示（如 message.warning），直接 return 无声失败。
- **P3 代码质量 (SmartFieldMapper/index.tsx:31)**: `useEffect` 依赖只有 `[batchId]`，但 `fetchMappings` 不在依赖中（虽然因为 batchId 不变时 fetchMappings 引用也不变，但 ESLint 可能会警告）。

**代码质量评价**: 8/10 — 字段映射逻辑完整，UI 交互清晰。

---

### 20. `frontend-web/src/components/Layout/index.tsx`
**主要功能**: 应用主布局，侧边栏 + 头部 + 内容区域。

**发现的问题**:
- **P3 代码质量 (Layout/index.tsx:153)**: 通知 Badge `count={0}` 固定为 0，通知功能未实现。空 Badge 可以隐藏或移除。
- **P3 代码质量 (Layout/index.tsx:80-81)**: "个人设置" 菜单项点击没有对应处理函数，会触发 `handleMenuClick` 但 key 是 'profile' 不是路由路径。

**代码质量评价**: 8/10 — 布局结构标准规范。

---

### 21. `frontend-web/src/components/TrendChart/index.tsx`
**主要功能**: 基于 ECharts 的趋势折线图组件。

**发现的问题**:
- **P3 代码质量 (TrendChart/index.tsx:37)**: `const series: any[]` — 使用 any 类型，失去了 ECharts 类型安全。
- **P3 代码质量**: 整体封装质量高，useMemo 优化了 option 计算，双 Y 轴配置合理。

**代码质量评价**: 8/10 — ECharts 封装专业。

---

### 22. `frontend-web/src/components/RoiCard/index.tsx`
**主要功能**: ROI 指标卡片，展示数值和趋势箭头。

**发现的问题**:
- **P3 代码质量 (RoiCard/index.tsx:56-59)**: 趋势方向判断基于 `title.includes('花费') || title.includes('CPL')`，依赖中文标题文本，如果标题文案修改会导致逻辑错误。建议增加一个 `inverseTrend` prop。

**代码质量评价**: 8/10 — 组件简洁实用。

---

### 23. `frontend-web/src/components/AttributionConfirm/index.tsx`
**主要功能**: 归因规则确认弹窗。

**发现的问题**:
- **P1 运行时错误 (AttributionConfirm/index.tsx:152)**: **使用了 `ArrowRightOutlined` 但 import 语句在文件末尾（第227行）。** 虽然 ESLint 可能允许，但 import 语句应在文件顶部。某些打包工具或严格配置下可能导致运行时错误。
- **P2 逻辑隐患 (AttributionConfirm/index.tsx:65-67)**: `handleConfirm` 检查 `confirmed` 复选框，但 `onConfirm` 传递的是 `selectedRules`（归因规则映射），而 CRM 页面的 `handleMappingConfirm` 将其传给 `crmApi.confirmMapping`（字段映射 API）。数据语义不匹配。

**代码质量评价**: 6/10 — import 位置错误是严重问题，数据流语义混淆。

---

## 六、类型定义和工具

### 24. `frontend-web/src/types/index.ts`
**主要功能**: 前端类型定义，与后端 Pydantic Schema 对应。

**发现的问题**:
- **P3 代码质量 (types/index.ts:279-291)**: `ApiResponse<T>` 和 `PaginatedResponse<T>` 定义了但实际 API 层未使用。API 调用直接使用具体类型（如 `axiosInstance.get<DashboardMetrics>`），返回的是 AxiosResponse。如果后端将来切换到 `{ data, code, message }` 包装格式，所有 API 调用都需要修改。
- **P3 代码质量**: 类型覆盖全面，与后端对应良好。

**代码质量评价**: 8/10 — 类型定义完整。

---

### 25. `frontend-web/src/utils/formatters.ts`
**主要功能**: 格式化工具函数（货币、数字、百分比、日期等）。

**发现的问题**:
- **P3 代码质量 (formatters.ts:86-93)**: `formatFileSize` 中 `Math.log(bytes)` 当 `bytes <= 0` 时返回 NaN。虽然第87行有 `bytes === 0` 的处理，但负数没有处理。
- **P3 代码质量**: 函数设计合理，覆盖常见场景。

**代码质量评价**: 9/10 — 工具函数质量高。

---

### 26. `frontend-web/src/utils/fieldMatcher.ts`
**主要功能**: 智能字段匹配算法（编辑距离 + 别名匹配）。

**发现的问题**:
- **P3 代码质量 (fieldMatcher.ts:45)**: `Array(len1 + 1).fill(null).map(...)` — 每次创建二维数组，对于长字符串性能不佳。但列名通常不长，实际影响极小。
- **P3 代码质量 (fieldMatcher.ts:118)**: `requiredFields = ['name', 'phone']` 在函数内部硬编码，如果后续增加必填字段需要修改此处和 SmartFieldMapper 中的相同硬编码。建议提取为常量。

**代码质量评价**: 8/10 — 算法实现正确，模糊匹配效果好。

---

### 27. `frontend-web/src/App.tsx`
**主要功能**: 主应用组件，路由配置。

**发现的问题**:
- **P2 逻辑隐患 (App.tsx:25-27,57-59)**: `ProtectedRoute` 和 `PublicRoute` 都调用了 `checkAuth()`，但 `checkAuth` 是异步的且没有去重。应用挂载时两个路由可能并发触发。
- **P2 逻辑隐患 (App.tsx:63-73)**: `PublicRoute` 中已认证用户跳转逻辑：先调用 `fetchStatus()`（异步），然后根据结果决定跳转到 `/dashboard` 或 `/onboarding`。但这个逻辑和后面的 `return <Navigate to="/dashboard" replace />`（第88行）矛盾。第88行的 Navigate 总是跳转到 `/dashboard`，而 fetchStatus 的回调可能跳转到 `/onboarding`。由于 fetchStatus 是异步的，第88行会先执行跳转到 dashboard，然后 fetchStatus 完成后又尝试跳转，导致路由闪烁。
- **P3 代码质量 (App.tsx:136)**: 404 路由重定向到 `/dashboard`，但 `/dashboard` 是受保护路由，如果未认证用户访问 404 会跳到登录页。行为合理但可以更明确。

**代码质量评价**: 6/10 — 路由守卫逻辑有竞态和闪烁问题。

---

## 七、整体评估

### 关键发现汇总

| 级别 | 数量 | 摘要 |
|------|------|------|
| P0 阻断 | 0 | 无 |
| P1 运行时错误 | 1 | AttributionConfirm 中 ArrowRightOutlined import 在文件末尾 |
| P2 逻辑隐患 | 12 | 详见各文件分析 |
| P3 代码质量 | 18+ | 类型安全、代码风格、未完成功能等 |

### 最需要优先修复的 P1/P2 问题

1. **P1 - AttributionConfirm import 位置** (AttributionConfirm/index.tsx:227): 将 `ArrowRightOutlined` 的 import 移到文件顶部。

2. **P2 - Dashboard 时间范围切换不刷新数据** (dashboard/index.tsx:80-83,168): `handleTimeRangeChange` 和 `RangePicker.onChange` 需要触发 `fetchData()`。

3. **P2 - Analytics 日期筛选无效** (analytics/index.tsx:211-213): 同上，RangePicker 变更需触发数据请求。

4. **P2 - CRM 归因规则与字段映射数据流混淆** (crm/index.tsx:124-135, AttributionConfirm): `AttributionConfirm.onConfirm` 传出的是归因规则，但被传给了 `confirmMapping`（字段映射 API）。

5. **P2 - App.tsx 路由闪烁** (App.tsx:63-88): PublicRoute 中 fetchStatus 异步跳转与同步 Navigate 冲突。

6. **P2 - Settings 账户设置功能未实现** (settings/index.tsx:203-216): 表单纯静态，无数据绑定和提交逻辑。

7. **P2 - Reports 下载文件扩展名判断错误** (reports/index.tsx:92): `report_type` 中不存在 'excel'，永远下载为 .pdf。

8. **P2 - CRM 页面 filters 依赖可能无限循环** (crm/index.tsx:94-97): `filters` 对象引用每次渲染都变化。

9. **P2 - Token 双写潜在不一致** (authStore.ts:39-40,122-128): localStorage 和 zustand persist 同时存储 token。

10. **P2 - request.ts baseURL 硬编码** (request.ts:51): Token 刷新请求的 URL 不受 `VITE_API_BASE_URL` 控制。

### 架构层面评价

- **项目结构**: 清晰的分层（API → Store → Pages → Components），职责划分合理。
- **类型系统**: 类型定义完整，与后端对应良好，但 API 层部分调用缺少返回类型注解。
- **状态管理**: Zustand 使用得当，persist 中间件合理使用。但 Auth Store 的 Token 管理有双写问题。
- **错误处理**: 全局 Axios 拦截器处理了常见 HTTP 错误，但各页面的 catch 块处理方式不统一（有的用 message.error，有的用 console.error）。
- **组件复用**: RoiCard、TrendChart、EmptyState 等组件复用性好，Props 类型定义清晰。
- **路由守卫**: ProtectedRoute/PublicRoute 设计合理，但有并发 checkAuth 和路由闪烁问题。
结果
消息已发送给 当前 Agent。
Reportsent.Nowletmecheckifthereareanytasksavailable.Report sent. Now let me check if there are any tasks available.

Alltasksarecompleted.Mycomprehensivefrontendcodereviewreporthasbeensenttotheteamlead,coveringall27filesacross6categories(APIlayer,Storelayer,Pages,Hooks,Components,Types/Utils)with1P1issue,12P2issues,and18+P3issuesidentified.All tasks are completed. My comprehensive frontend code review report has been sent to the team lead, covering all 27 files across 6 categories (API layer, Store layer, Pages, Hooks, Components, Types/Utils) with 1 P1 issue, 12 P2 issues, and 18+ P3 issues identified.
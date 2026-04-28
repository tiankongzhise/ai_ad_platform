# 前端BUG修复清单

## 修复概览

| BUG编号 | 严重性 | 问题描述 | 文件 | 状态 |
|---------|--------|---------|------|------|
| P1-5 | 🟠 P1 | previewMapping HTTP method 应为 POST | `frontend-web/src/api/index.ts` | ✅ 已修复 |
| P2-6 | 🟡 P2 | CRM 字段映射与归因弹窗逻辑反向 | `frontend-web/src/pages/crm/index.tsx` | ✅ 已修复 |
| P2-7 | 🟡 P2 | handleViewDemo 使用 getState() 问题 | `frontend-web/src/pages/dashboard/index.tsx` | ✅ 已修复 |

## 已验证无需修复的BUG

| BUG编号 | 问题描述 | 验证结果 |
|---------|---------|---------|
| P1-1 | OAuth 绑定使用 window.open | ✅ 代码第98行已使用 `window.location.href` |
| P1-3 | DashboardPage 解析 timeRange 为 parseInt | ✅ 代码第40行使用 `useState<number>(30)`，选项值也是数字 |
| P1-4 | CRM 上传弹窗 beforeUpload 返回 false | ✅ 代码第319行只有 `customRequest={handleUpload}`，无 beforeUpload |
| P1-6 | OAuth 回调结果未处理 | ✅ 代码第60-83行已处理 oauth_result 参数 |
| P2-2 | EmptyState scenario 类型不一致 | ✅ EmptyState 组件已使用 `scenario: DashboardStatus` 类型 |
| P3-1 | Token 刷新逻辑竞态条件 | ✅ 代码第8-68行已有刷新锁实现 |

## 修复详情

### 1. P1-5: previewMapping HTTP method 应为 POST
- **文件**: `frontend-web/src/api/index.ts`
- **修改**: 第137行 `axiosInstance.get` → `axiosInstance.post`
- **影响**: CRM 字段映射预览功能

### 2. P2-6: CRM 字段映射与归因弹窗逻辑反向
- **文件**: `frontend-web/src/pages/crm/index.tsx`
- **修改**:
  - 新增 `confirmedMappings` 状态存储字段映射
  - 修改上传成功后只关闭上传弹窗，不打开归因弹窗
  - 拆分 `handleMappingConfirm` 和 `handleAttributionConfirm`
  - 正确流程：上传 → 字段映射 → 归因确认 → 导入
- **影响**: CRM 上传导入完整流程

### 3. P2-7: handleViewDemo 使用 getState() 问题
- **文件**: `frontend-web/src/pages/dashboard/index.tsx`
- **修改**: 从 hook 直接解构 `enableDemoMode`，移除 `getState()` 调用
- **影响**: 演示数据切换功能

---

*清单生成时间: 2026-04-28*
*负责人: 前端开发*

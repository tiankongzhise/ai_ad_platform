# 前端BUG修复报告

> **项目名称**: EduAdCRM MVP  
> **报告时间**: 2026-04-28  
> **报告人**: 前端开发负责人  
> **审核依据**: CODE_REVIEW.md 代码审核报告

---

## 一、修复概述

根据 CODE_REVIEW.md 代码审核报告，本次针对前端代码共识别出 **9个潜在BUG**。经过代码审查与验证，其中：

- **3个BUG** 确实存在，已完成修复 ✅
- **6个BUG** 经核实代码已正确实现，无需修复 ✅

---

## 二、已修复BUG详情

### 1. P1-5: previewMapping HTTP Method 错误 🟠

| 项目 | 内容 |
|------|------|
| **严重性** | P1 - 运行时错误 |
| **问题描述** | `/crm/upload/{batch_id}/preview` 接口应使用 POST 方法，但前端实现为 GET |
| **涉及文件** | `frontend-web/src/api/index.ts` (第137行) |
| **修复方案** | 将 `axiosInstance.get` 改为 `axiosInstance.post` |
| **修复状态** | ✅ 已修复 |

**修复代码**:
```diff
- previewMapping: (batchId: string) =>
-   axiosInstance.get<FieldMappingResponse>(`/crm/upload/${batchId}/preview`),
+ previewMapping: (batchId: string) =>
+   axiosInstance.post<FieldMappingResponse>(`/crm/upload/${batchId}/preview`, {}),
```

---

### 2. P2-6: CRM 字段映射与归因弹窗逻辑反向 🟡

| 项目 | 内容 |
|------|------|
| **严重性** | P2 - 逻辑隐患 |
| **问题描述** | 上传成功后直接打开归因弹窗，跳过了字段映射弹窗 |
| **涉及文件** | `frontend-web/src/pages/crm/index.tsx` |
| **修复方案** | 重构弹窗流程：上传 → 字段映射 → 归因确认 → 导入 |
| **修复状态** | ✅ 已修复 |

**修复要点**:
1. 新增 `confirmedMappings` 状态存储用户确认的字段映射
2. 修改上传成功后只关闭上传弹窗，不直接打开归因弹窗
3. 拆分为两个处理函数：
   - `handleMappingConfirm`: 存储映射并打开归因弹窗
   - `handleAttributionConfirm`: 合并映射+规则并调用API

**正确流程**:
```
上传成功 → 显示字段映射弹窗 → 确认映射 → 显示归因弹窗 → 确认归因 → 开始导入
```

---

### 3. P2-7: handleViewDemo 使用 getState() 问题 🟡

| 项目 | 内容 |
|------|------|
| **严重性** | P2 - 代码质量 |
| **问题描述** | 在事件处理函数中调用 `useDemoStore.getState()` 获取 action |
| **涉及文件** | `frontend-web/src/pages/dashboard/index.tsx` (第99-103行) |
| **修复方案** | 从 hook 直接解构 `enableDemoMode` |
| **修复状态** | ✅ 已修复 |

**修复代码**:
```diff
- const { isDemoMode, demoData, fetchDemoData } = useDemoStore();
+ const { isDemoMode, demoData, fetchDemoData, enableDemoMode } = useDemoStore();

  const handleViewDemo = () => {
-   const { enableDemoMode } = useDemoStore.getState();
    enableDemoMode();
  };
```

---

## 三、经核实无需修复项

以下BUG经代码核实，**代码已正确实现**，无需修复：

| BUG编号 | 问题描述 | 核实结果 |
|---------|---------|---------|
| P1-1 | OAuth 绑定使用 window.open | ✅ 代码第98行已使用 `window.location.href` |
| P1-3 | Dashboard timeRange parseInt | ✅ 使用 `useState<number>(30)`，选项值为数字 |
| P1-4 | Upload beforeUpload 返回 false | ✅ 只有 `customRequest`，无 beforeUpload |
| P1-6 | OAuth 回调结果未处理 | ✅ 第60-83行已处理 oauth_result 参数 |
| P2-2 | EmptyState scenario 类型 | ✅ 组件已使用 `scenario: DashboardStatus` 类型 |
| P3-1 | Token 刷新竞态条件 | ✅ 第8-68行已有刷新锁实现 |

---

## 四、修复文件清单

| 序号 | 文件路径 | 修改类型 |
|------|---------|---------|
| 1 | `frontend-web/src/api/index.ts` | 修改 |
| 2 | `frontend-web/src/pages/crm/index.tsx` | 修改 |
| 3 | `frontend-web/src/pages/dashboard/index.tsx` | 修改 |

---

## 五、BUG修复记录文档

每个修复的BUG都创建了单独的记录文档，位于 `frontend_bug_fix/` 目录：

| 文档名称 | 对应BUG |
|---------|--------|
| `P1-5-previewMapping-HTTP-Method.md` | P1-5 |
| `P2-6-CRM-字段映射与归因弹窗逻辑.md` | P2-6 |
| `P2-7-handleViewDemo-getState问题.md` | P2-7 |

---

## 六、验证建议

### 功能测试清单

1. **CRM 上传导入流程**
   - [ ] 上传 Excel 文件
   - [ ] 验证字段映射弹窗正常显示
   - [ ] 确认映射后验证归因弹窗正常显示
   - [ ] 确认归因后验证导入任务提交成功

2. **Dashboard 演示模式**
   - [ ] 点击"先看看演示数据"按钮
   - [ ] 验证页面正常切换到演示模式

3. **OAuth 授权流程**（需后端支持）
   - [ ] 点击绑定广告账户
   - [ ] 验证整页跳转到授权页
   - [ ] 授权完成后验证返回状态处理

---

## 七、后端配合需求

以下修复需要后端同步支持：

| 前端修复 | 后端需求 |
|---------|---------|
| P1-5 previewMapping POST | 后端 `/crm/upload/{batch_id}/preview` 需支持 POST 方法 |

---

## 八、总结

本次前端BUG修复工作已完成：

- **修复数量**: 3个
- **无需修复**: 6个
- **修复率**: 100%
- **代码质量提升**: 统一了 store 调用风格，修复了逻辑流程问题

所有修复均已记录在案，并提供了详细的验证方案。

---

*报告生成时间: 2026-04-28*  
*前端开发负责人*

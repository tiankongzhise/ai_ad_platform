# BUG修复记录: P2-7 handleViewDemo使用getState()问题

## 基本信息
- **BUG编号**: P2-7
- **发现时间**: 2026-04-28
- **审核报告**: CODE_REVIEW.md
- **修复时间**: 2026-04-28
- **状态**: ✅ 已修复

## 问题描述
`handleViewDemo` 函数在事件处理函数中调用 `useDemoStore.getState()` 获取 action，风格上与其他 store 使用方式不一致。

## 问题代码
文件: `frontend-web/src/pages/dashboard/index.tsx` 第99-103行

```tsx
const handleViewDemo = () => {
  // 切换到演示模式
  const { enableDemoMode } = useDemoStore.getState();  // ← 在事件处理器中调用 getState()
  enableDemoMode();
};
```

## 问题分析
1. `DashboardPage` 顶部已经从 `useDemoStore` 解构了 `isDemoMode`、`demoData`、`fetchDemoData`
2. 但 `enableDemoMode` 没有从 hook 中解构，而是在事件处理器中用 `getState()` 获取
3. 虽然 Zustand 允许在事件处理函数中使用 `getState()`，但这与其他 store 使用方式不一致

## 修复方案
从 `useDemoStore` hook 中直接解构 `enableDemoMode`

## 修复前代码
```tsx
const { isDemoMode, demoData, fetchDemoData } = useDemoStore();

// ...

const handleViewDemo = () => {
  const { enableDemoMode } = useDemoStore.getState();
  enableDemoMode();
};
```

## 修复后代码
```tsx
const { isDemoMode, demoData, fetchDemoData, enableDemoMode } = useDemoStore();

// ...

const handleViewDemo = () => {
  // 切换到演示模式
  enableDemoMode();
};
```

## 影响范围
- DashboardPage 演示数据切换功能
- EmptyState 组件的"先看看演示数据"按钮

## 关联BUG
无直接关联

## 验证方式
1. 进入 Dashboard 页面
2. 如果显示空态，点击"先看看演示数据"按钮
3. 检查页面是否正常切换到演示模式并显示演示数据

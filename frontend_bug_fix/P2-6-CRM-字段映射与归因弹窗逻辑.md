# BUG修复记录: P2-6 CRM字段映射与归因弹窗逻辑反向

## 基本信息
- **BUG编号**: P2-6
- **发现时间**: 2026-04-28
- **审核报告**: CODE_REVIEW.md
- **修复时间**: 2026-04-28
- **状态**: ✅ 已修复

## 问题描述
CRM 页面字段映射弹窗与归因确认弹窗的显示逻辑相反，导致上传流程混乱：
1. 上传成功后直接打开了归因弹窗，跳过了字段映射弹窗
2. 字段映射弹窗的显示条件 `open={!!currentBatchId && !attributionModalVisible}` 逻辑不正确

## 正确流程
```
上传成功 → 显示字段映射弹窗 → 确认映射 → 显示归因弹窗 → 确认归因 → 开始导入
```

## 问题代码
文件: `frontend-web/src/pages/crm/index.tsx`

### 问题1: 上传成功后直接打开归因弹窗
```tsx
// 第114-115行
setUploadModalVisible(false);
setAttributionModalVisible(true);  // ← 直接打开了归因弹窗，跳过了字段映射！
```

### 问题2: 字段映射弹窗显示条件
```tsx
// 第335行
open={!!currentBatchId && !attributionModalVisible}  // 逻辑反了
```

### 问题3: handleMappingConfirm 直接调用 crmApi.confirmMapping
```tsx
// 原逻辑直接确认映射并调用API
const handleMappingConfirm = (mappings) => {
  setAttributionModalVisible(false);
  // 直接调用确认映射
  crmApi.confirmMapping(currentBatchId, mappings)...
};
```

## 修复方案

### 1. 修改上传成功后的逻辑
移除 `setAttributionModalVisible(true)`，先显示字段映射弹窗

### 2. 添加状态存储字段映射
添加 `confirmedMappings` 状态存储用户确认的字段映射

### 3. 拆分为两个处理函数
- `handleMappingConfirm`: 存储映射并打开归因弹窗
- `handleAttributionConfirm`: 合并映射+规则并调用API

## 修复后代码

### 新增状态
```tsx
// 存储字段映射（用于传递给归因确认后的导入）
const [confirmedMappings, setConfirmedMappings] = useState<Record<string, string> | null>(null);
```

### 修改上传处理
```tsx
message.success('文件上传成功，正在解析...');
setUploadModalVisible(false);
// 先显示字段映射弹窗（不直接打开归因弹窗）
setUploadFileList([]);
```

### 新增字段映射确认处理
```tsx
// 处理字段映射确认
const handleMappingConfirm = (mappings: Record<string, string>) => {
  // 存储字段映射，确认归因后使用
  setConfirmedMappings(mappings);
  // 确认字段映射后，显示归因确认弹窗
  setAttributionModalVisible(true);
};

// 处理归因确认并开始导入
const handleAttributionConfirm = (rules: Record<string, string>) => {
  if (currentBatchId && confirmedMappings) {
    // 合并字段映射和归因规则
    const combinedMappings = {
      ...confirmedMappings,
      ...rules,
    };
    crmApi.confirmMapping(currentBatchId, combinedMappings).then(() => {
      message.success('导入任务已提交');
      fetchBatches();
      // 清理状态
      setAttributionModalVisible(false);
      setCurrentBatchId(null);
      setConfirmedMappings(null);
      setUploadFileList([]);
    }).catch(() => {
      message.error('导入失败');
    });
  }
};
```

## 影响范围
- CRM 页面上传导入功能
- SmartFieldMapper 组件
- AttributionConfirm 组件

## 关联BUG
- P1-4: CRM 上传弹窗 beforeUpload 返回 false（可能需要检查）
- P1-5: previewMapping HTTP method（已修复）

## 验证方式
1. 进入 CRM 页面
2. 点击"导入线索"按钮
3. 上传 Excel 文件
4. 检查是否先显示"确认字段映射"弹窗
5. 确认映射后检查是否显示"归因规则确认"弹窗
6. 确认归因后检查是否提交导入任务

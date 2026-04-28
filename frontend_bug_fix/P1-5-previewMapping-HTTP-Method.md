# BUG修复记录: P1-5 previewMapping HTTP Method错误

## 基本信息
- **BUG编号**: P1-5
- **发现时间**: 2026-04-28
- **审核报告**: CODE_REVIEW.md
- **修复时间**: 2026-04-28
- **状态**: ✅ 已修复

## 问题描述
文档要求 `/crm/upload/{batch_id}/preview` 为 `POST` 方法，但前端实现为 `GET` 方法。

## 问题代码
文件: `frontend-web/src/api/index.ts` 第136-137行
```typescript
/** 预览字段映射 */
previewMapping: (batchId: string) =>
  axiosInstance.get<FieldMappingResponse>(`/crm/upload/${batchId}/preview`),
```

## 问题分析
1. 技术文档 §6.2 明确定义为 `POST /api/v1/crm/upload/{batch_id}/preview`
2. 预览操作需要在服务端触发字段分析（有副作用），应为 `POST` 而非 `GET`
3. `GET` 方法按 HTTP 规范不应有副作用

## 修复方案
将 `axiosInstance.get` 改为 `axiosInstance.post`，并传入空请求体 `{}`

## 修复后代码
```typescript
/** 预览字段映射 */
previewMapping: (batchId: string) =>
  axiosInstance.post<FieldMappingResponse>(`/crm/upload/${batchId}/preview`, {}),
```

## 影响范围
- CRM 页面字段映射预览功能
- 后端需同步更新路由支持 POST 方法

## 关联BUG
- P0-2: 后端缺少 crm.py 路由文件（需同步修复）

## 验证方式
1. 启动后端服务（需先实现 crm 路由）
2. 在 CRM 页面上传 Excel 文件
3. 检查字段映射弹窗是否能正常显示预览数据

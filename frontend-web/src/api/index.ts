/**
 * API 接口封装
 * 与后端 FastAPI 路由一一对应
 */
import axiosInstance from './request';
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  User,
  AdAccount,
  AdAccountListResponse,
  OAuthCallbackResponse,
  SyncStatusResponse,
  ManualSyncRequest,
  ManualSyncResponse,
  DemoDashboardResponse,
  OnboardingStatus,
  OnboardingUpdateRequest,
  ImportProgress,
  FieldMappingResponse,
  AttributionSuggestion,
  CRMLead,
  DashboardStatusResponse,
  DashboardMetrics,
  TrendDataPoint,
  ChannelComparison,
  CrossTableRow,
  Report,
  InsightCard,
} from '@/types';

// ==================== 认证模块 ====================
export const authApi = {
  /** 登录 */
  login: (data: LoginRequest) =>
    axiosInstance.post<LoginResponse>('/auth/login', data),

  /** 注册 */
  register: (data: RegisterRequest) =>
    axiosInstance.post<{ message: string }>('/auth/register', data),

  /** 刷新 Token */
  refresh: (refreshToken: string) =>
    axiosInstance.post<{ access_token: string }>('/auth/refresh', { refresh_token: refreshToken }),

  /** 登出 */
  logout: () =>
    axiosInstance.post<{ message: string }>('/auth/logout'),

  /** 获取当前用户信息 */
  getProfile: () =>
    axiosInstance.get<User>('/auth/profile'),
};

// ==================== 演示数据模块 ====================
export const demoApi = {
  /** 获取演示仪表盘数据 */
  getDashboard: () =>
    axiosInstance.get<DemoDashboardResponse>('/demo/dashboard'),

  /** 获取演示核心指标 */
  getMetrics: () =>
    axiosInstance.get<DemoDashboardResponse['metrics']>('/demo/metrics'),
};

// ==================== 引导状态模块 ====================
export const onboardingApi = {
  /** 获取引导进度 */
  getStatus: () =>
    axiosInstance.get<OnboardingStatus>('/onboarding/status'),

  /** 更新引导状态 */
  updateStatus: (data: OnboardingUpdateRequest) =>
    axiosInstance.post<OnboardingStatus>('/onboarding/status', data),

  /** 完成引导 */
  complete: () =>
    axiosInstance.post<{ message: string }>('/onboarding/complete'),
};

// ==================== 广告账户模块 ====================
export const adAccountApi = {
  /** 获取广告账户列表 */
  list: (params?: { platform?: string; status?: string }) =>
    axiosInstance.get<AdAccountListResponse>('/ad/accounts', { params }),

  /** 获取单个广告账户 */
  get: (accountId: string) =>
    axiosInstance.get<AdAccount>(`/ad/accounts/${accountId}`),

  /** 删除广告账户 */
  delete: (accountId: string) =>
    axiosInstance.delete(`/ad/accounts/${accountId}`),

  /** 获取巨量引擎 OAuth URL */
  getJuliangOAuthUrl: () =>
    axiosInstance.get<{ oauth_url: string; state: string }>('/ad/juliang/oauth-url'),

  /** 巨量引擎 OAuth 回调（前端处理，不需要手动调用） */
  juliangCallback: (code: string, state?: string) =>
    axiosInstance.get<OAuthCallbackResponse>('/ad/juliang/callback', { params: { code, state } }),

  /** 获取百度营销 OAuth URL */
  getBaiduOAuthUrl: () =>
    axiosInstance.get<{ oauth_url: string; state: string }>('/ad/baidu/oauth-url'),

  /** 手动触发同步 */
  manualSync: (accountId: string, data: ManualSyncRequest) =>
    axiosInstance.post<ManualSyncResponse>(`/ad/accounts/${accountId}/sync`, data),

  /** 获取同步状态 */
  getSyncStatus: () =>
    axiosInstance.get<SyncStatusResponse>('/ad/sync-status'),
};

// ==================== CRM 模块 ====================
export const crmApi = {
  /** 上传 Excel/CSV 文件 */
  upload: (formData: FormData, onProgress?: (percent: number) => void) =>
    axiosInstance.post<{ batch_id: string; task_id: string }>('/crm/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percent);
        }
      },
    }),

  /** 获取上传任务进度 */
  getUploadProgress: (taskId: string) =>
    axiosInstance.get<ImportProgress>(`/crm/upload/${taskId}`),

  /** 预览字段映射 */
  previewMapping: (batchId: string) =>
    axiosInstance.post<FieldMappingResponse>(`/crm/upload/${batchId}/preview`, {}),

  /** 确认字段映射并开始导入 */
  confirmMapping: (batchId: string, mappings: Record<string, string>) =>
    axiosInstance.post(`/crm/upload/${batchId}/confirm`, { field_mappings: mappings }),

  /** 获取归因建议 */
  getAttributionSuggest: (batchId: string) =>
    axiosInstance.get<AttributionSuggestion>(`/crm/upload/${batchId}/attribution-suggest`),

  /** 获取线索列表 */
  getLeads: (params?: { page?: number; page_size?: number; deal_status?: string }) =>
    axiosInstance.get<{ items: CRMLead[]; total: number }>('/crm/leads', { params }),

  /** 更新线索状态 */
  updateLead: (leadId: string, data: Partial<CRMLead>) =>
    axiosInstance.patch<CRMLead>(`/crm/leads/${leadId}`, data),

  /** 删除导入批次 */
  deleteBatch: (batchId: string) =>
    axiosInstance.delete(`/crm/batches/${batchId}`),

  /** 获取导入批次列表 */
  getBatches: () =>
    axiosInstance.get<{ items: ImportProgress[] }>('/crm/batches'),
};

// ==================== 分析模块 ====================
export const analyticsApi = {
  /** 获取仪表盘数据 */
  getDashboard: () =>
    axiosInstance.get<DashboardMetrics>('/analytics/dashboard'),

  /** 获取仪表盘状态（决定空态场景） */
  getDashboardStatus: () =>
    axiosInstance.get<DashboardStatusResponse>('/analytics/dashboard/status'),

  /** 获取趋势数据 */
  getTrend: (params?: { days?: number }) =>
    axiosInstance.get<TrendDataPoint[]>('/analytics/trend', { params }),

  /** 获取渠道对比数据 */
  getChannelCompare: () =>
    axiosInstance.get<ChannelComparison[]>('/analytics/channel-compare'),

  /** 获取交叉分析数据 */
  getCrossTable: (params?: { page?: number; page_size?: number }) =>
    axiosInstance.get<{ items: CrossTableRow[]; total: number }>('/analytics/cross-table', { params }),

  /** 导出交叉分析数据 */
  exportCrossTable: (params?: { start_date?: string; end_date?: string }) =>
    axiosInstance.get('/analytics/cross-table/export', {
      params,
      responseType: 'blob',
    }),
};

// ==================== 报表模块 ====================
export const reportsApi = {
  /** 生成报表 */
  generate: (data: { report_type: string; start_date: string; end_date: string }) =>
    axiosInstance.post<{ task_id: string }>('/reports/generate', data),

  /** 获取报表列表 */
  list: () =>
    axiosInstance.get<Report[]>('/reports'),

  /** 下载报表 */
  download: (reportId: string) =>
    axiosInstance.get(`/reports/${reportId}/download`, {
      responseType: 'blob',
    }),

  /** 获取报表行动建议 */
  getInsights: (reportId: string) =>
    axiosInstance.get<InsightCard[]>(`/reports/${reportId}/insights`),
};

// ==================== 设置模块 ====================
export const settingsApi = {
  /** 获取租户信息 */
  getTenant: () =>
    axiosInstance.get('/settings/tenant'),

  /** 更新租户信息 */
  updateTenant: (data: { name?: string; industry_sub_type?: string; main_product?: string }) =>
    axiosInstance.patch('/settings/tenant', data),

  /** 获取归因规则列表 */
  getAttributionRules: () =>
    axiosInstance.get('/settings/attribution-rules'),

  /** 创建归因规则 */
  createAttributionRule: (data: { platform: string; keywords: string[] }) =>
    axiosInstance.post('/settings/attribution-rules', data),

  /** 更新归因规则 */
  updateAttributionRule: (ruleId: string, data: Partial<{ keywords: string[] }>) =>
    axiosInstance.patch(`/settings/attribution-rules/${ruleId}`, data),

  /** 删除归因规则 */
  deleteAttributionRule: (ruleId: string) =>
    axiosInstance.delete(`/settings/attribution-rules/${ruleId}`),
};

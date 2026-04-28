/**
 * 前端类型定义
 * 与后端 Pydantic Schema 对应
 */

// ==================== 认证相关 ====================
export interface User {
  id: string;
  tenant_id: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface RegisterRequest {
  email: string;
  password: string;
  tenant_name: string;
}

// ==================== 广告账户相关 ====================
export type AdPlatform = 'juliang' | 'baidu';
export type AdAccountStatus = 'active' | 'suspended' | 'authorized' | 'expired' | 'error';

export interface AdAccount {
  id: string;
  tenant_id: string;
  platform: AdPlatform;
  account_id: string;
  account_name: string;
  balance: number;
  status: AdAccountStatus;
  token_expires_at?: string;
  created_at: string;
  updated_at: string;
}

export interface AdAccountListResponse {
  items: AdAccount[];
  total: number;
}

export interface OAuthCallbackResponse {
  status: string;
  ad_account_id: string;
  account_name: string;
  next_step: string;
  message: string;
}

export interface SyncStatusResponse {
  ad_accounts_bound: boolean;
  has_ad_data: boolean;
  sync_in_progress: boolean;
  last_sync_at?: string;
  sync_error?: string;
}

export interface ManualSyncRequest {
  days: number;
}

export interface ManualSyncResponse {
  task_id: string;
  message: string;
  estimated_completion: string;
}

// ==================== 演示数据相关 ====================
export interface DemoMetrics {
  today_spend: number;
  total_leads: number;
  cost_per_lead: number;
  roi: number;
  conversion_rate: number;
}

export interface DemoTrendData {
  date: string;
  spend: number;
  leads: number;
}

export interface DemoChannelData {
  platform: string;
  spend: number;
  leads: number;
  roi: number;
}

export interface DemoCampaignRanking {
  campaign_name: string;
  spend: number;
  leads: number;
  cpl: number;
  roi: number;
}

export interface DemoDashboardResponse {
  mode: 'demo';
  org_name: string;
  metrics: DemoMetrics;
  trends: DemoTrendData[];
  channel_compare: DemoChannelData[];
  campaign_ranking: DemoCampaignRanking[];
}

// ==================== 引导状态相关 ====================
export interface OnboardingStep1 {
  name: string;
  industry_sub_type: string;
  main_product: string;
}

export interface OnboardingStep2 {
  platforms: AdPlatform[];
}

export interface OnboardingStatus {
  tenant_id: string;
  step1_org_info?: OnboardingStep1;
  step2_ad_bound?: OnboardingStep2;
  step3_crm_imported: boolean;
  completed_at?: string;
}

export interface OnboardingUpdateRequest {
  step1_org_info?: OnboardingStep1;
  step2_ad_bound?: OnboardingStep2;
  step3_crm_imported?: boolean;
}

// ==================== CRM 导入相关 ====================
export type ImportStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface ImportBatch {
  id: string;
  tenant_id: string;
  filename: string;
  file_path: string;
  total_rows: number;
  success_rows: number;
  skip_rows: number;
  fail_rows: number;
  status: ImportStatus;
  created_at: string;
}

export interface ImportProgress {
  task_id: string;
  status: ImportStatus;
  progress: number;
  processed_rows: number;
  total_rows: number;
  message?: string;
}

export interface FieldMapping {
  field: string;
  matchedColumn?: string;
  confidence: 'auto' | 'suggested' | 'none';
}

export interface FieldMappingResponse {
  batch_id: string;
  columns: string[];
  field_mappings: FieldMapping[];
  unmatched_fields: string[];
}

export interface AttributionSuggestion {
  matched_count: number;
  unmatched_count: number;
  suggestions: {
    channel: string;
    count: number;
    matched_platform?: AdPlatform;
  }[];
  unmatched_sample: string[];
}

export interface CRMLead {
  id: string;
  batch_id: string;
  name: string;
  phone_hash: string;
  source_channel?: string;
  course_name?: string;
  deal_status: 'deal' | 'no_deal' | 'following';
  deal_amount?: number;
  deal_date?: string;
  raw_source_value?: string;
  created_at: string;
}

// ==================== 分析/仪表盘相关 ====================
export type DashboardStatus = 'scenario_a' | 'scenario_b' | 'scenario_c' | 'full_data';

export interface DashboardStatusResponse {
  status: DashboardStatus;
  has_ad_account: boolean;
  has_ad_data: boolean;
  has_crm_data: boolean;
  sync_in_progress: boolean;
}

export interface DashboardMetrics {
  total_spend: number;
  total_leads: number;
  cost_per_lead: number;
  roi: number;
  conversion_rate: number;
  spend_trend: number; // 百分比变化
  leads_trend: number;
}

export interface TrendDataPoint {
  date: string;
  spend: number;
  leads: number;
}

export interface ChannelComparison {
  platform: AdPlatform;
  spend: number;
  leads: number;
  cpl: number;
  roi: number;
}

export interface CrossTableRow {
  campaign_id: string;
  campaign_name: string;
  course_name?: string;
  spend: number;
  leads: number;
  deals: number;
  roi: number;
}

// ==================== 报表相关 ====================
export interface Report {
  id: string;
  tenant_id: string;
  report_type: string;
  date_range: {
    start: string;
    end: string;
  };
  status: 'generating' | 'ready' | 'failed';
  download_url?: string;
  created_at: string;
}

export interface InsightCard {
  id: string;
  type: 'opportunity' | 'warning' | 'info';
  title: string;
  description: string;
  action_text?: string;
  action_url?: string;
  priority: number;
}

// ==================== API 通用响应 ====================
export interface ApiResponse<T> {
  data?: T;
  code?: string;
  message?: string;
  detail?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

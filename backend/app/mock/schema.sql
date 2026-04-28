-- Mock 数据库文件: backend/mock_data.sqlite3

-- 演示仪表盘趋势数据（30天）
CREATE TABLE IF NOT EXISTS mock_dashboard_trend (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    date TEXT NOT NULL,           -- YYYY-MM-DD
    spend REAL DEFAULT 0,         -- 广告花费
    leads INTEGER DEFAULT 0,      -- 线索数
    deals INTEGER DEFAULT 0,      -- 成交数
    deal_amount REAL DEFAULT 0,   -- 成交金额
    platform TEXT,                -- 'juliang' | 'baidu' | 'combined'
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_trend_tenant_date ON mock_dashboard_trend(tenant_id, date);

-- 演示线索数据
CREATE TABLE IF NOT EXISTS mock_crm_leads (
    id TEXT PRIMARY KEY,          -- lead_xxx
    tenant_id TEXT NOT NULL,
    batch_id TEXT,                -- 导入批次
    name TEXT,
    phone_masked TEXT,            -- 138****8888
    phone_hash TEXT,              -- SHA256 用于去重
    source_channel TEXT,          -- '抖音' | '百度' | '微信' | '其他'
    course_name TEXT,
    deal_status TEXT DEFAULT 'following', -- 'deal' | 'no_deal' | 'following'
    deal_amount REAL DEFAULT 0,
    attribution_rule_id TEXT,
    created_at TEXT,
    updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_leads_tenant ON mock_crm_leads(tenant_id);
CREATE INDEX IF NOT EXISTS idx_leads_batch ON mock_crm_leads(batch_id);

-- 导入批次记录
CREATE TABLE IF NOT EXISTS mock_crm_batches (
    id TEXT PRIMARY KEY,          -- batch_xxx
    tenant_id TEXT NOT NULL,
    filename TEXT,
    total_rows INTEGER DEFAULT 0,
    processed_rows INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending', -- 'pending' | 'processing' | 'completed' | 'failed'
    mapping_confirmed INTEGER DEFAULT 0,
    attribution_confirmed INTEGER DEFAULT 0,
    created_at TEXT,
    completed_at TEXT
);

-- 演示报表
CREATE TABLE IF NOT EXISTS mock_reports (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    report_type TEXT,             -- 'daily' | 'weekly' | 'monthly'
    date_range_start TEXT,
    date_range_end TEXT,
    status TEXT DEFAULT 'ready',  -- 'generating' | 'ready' | 'failed'
    file_path TEXT,               -- 模拟文件路径
    insights TEXT,                -- JSON 行动建议
    created_at TEXT
);

-- 引导状态
CREATE TABLE IF NOT EXISTS mock_onboarding (
    tenant_id TEXT PRIMARY KEY,
    step1_done INTEGER DEFAULT 0,
    step1_org_name TEXT,
    step1_industry TEXT,
    step2_done INTEGER DEFAULT 0,  -- 广告账户绑定
    step3_done INTEGER DEFAULT 0,  -- CRM 导入
    completed_at TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 归因规则
CREATE TABLE IF NOT EXISTS mock_attribution_rules (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    name TEXT,
    platform TEXT,
    keywords TEXT,                -- JSON ["关键词1", "关键词2"]
    priority INTEGER DEFAULT 0,
    created_at TEXT
);

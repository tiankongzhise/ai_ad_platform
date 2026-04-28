"""
Mock 数据生成脚本
生成"星海教育"演示数据集
"""
import random
import secrets
from datetime import datetime, timedelta
from pathlib import Path

DEMO_CONFIG = {
    "org_name": "星海教育",
    "industry": "K12教育",
    "daily_spend_range": (8000, 15000),
    "cpe_range": (30, 50),
    "roi_range": (3.0, 6.0),
    "juliang_spend_ratio": 0.6,
    "baidu_spend_ratio": 0.4,
    "total_leads_30d": 1200,
    "deal_rate": 0.18,
    "courses": ["小学数学", "初中英语", "高中物理", "少儿编程"],
    "channels": ["抖音", "百度", "微信朋友圈", "知乎"],
}


async def generate_all_demo_data():
    """生成全套演示数据"""
    from .mock_db import get_mock_db
    
    # 使用固定的 tenant_id（演示专用）
    demo_tenant_id = "ten_demo_xinghai"
    
    async with get_mock_db() as db:
        # 1. 生成 30 天趋势数据
        await _generate_30d_trend(db, demo_tenant_id)
        
        # 2. 生成 500 条线索
        await _generate_crm_leads(db, demo_tenant_id)
        
        # 3. 生成 3 份报表
        await _generate_reports(db, demo_tenant_id)
        
        # 4. 初始化引导状态
        await _init_onboarding(db, demo_tenant_id)
        
        # 5. 生成归因规则
        await _generate_attribution_rules(db, demo_tenant_id)
        
        await db.commit()


async def _generate_30d_trend(db, tenant_id: str):
    """生成30天仪表盘数据"""
    base_date = datetime.now() - timedelta(days=30)
    
    for i in range(30):
        date = base_date + timedelta(days=i)
        
        # 抖音数据 (60%)
        jl_spend = random.uniform(4800, 9000)
        jl_leads = int(jl_spend / random.uniform(30, 50))
        
        # 百度数据 (40%)
        bd_spend = random.uniform(3200, 6000)
        bd_leads = int(bd_spend / random.uniform(35, 55))
        
        total_spend = jl_spend + bd_spend
        total_leads = jl_leads + bd_leads
        total_deals = int(total_leads * 0.18)
        total_deal_amount = total_deals * random.uniform(4000, 6000)
        
        await db.execute(
            """INSERT INTO mock_dashboard_trend 
               (tenant_id, date, spend, leads, deals, deal_amount, platform)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (tenant_id, date.strftime("%Y-%m-%d"), 
             round(total_spend, 2), total_leads, total_deals, 
             round(total_deal_amount, 2), "combined")
        )


async def _generate_crm_leads(db, tenant_id: str):
    """生成500条模拟线索"""
    surnames = ['张', '李', '王', '赵', '刘', '陈', '杨', '黄', '周', '吴']
    
    for i in range(500):
        name = f"{random.choice(surnames)}{random.randint(1, 100)}"
        phone_suffix = random.randint(10000000, 99999999)
        
        await db.execute(
            """INSERT INTO mock_crm_leads 
               (id, tenant_id, name, phone_masked, source_channel, 
                course_name, deal_status, deal_amount, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                f"lead_{secrets.token_hex(8)}",
                tenant_id,
                name,
                f"138****{phone_suffix % 10000:04d}",
                random.choice(DEMO_CONFIG["channels"]),
                random.choice(DEMO_CONFIG["courses"]),
                random.choices(
                    ["deal", "no_deal", "following"], 
                    weights=[0.18, 0.42, 0.40]
                )[0],
                round(random.uniform(3000, 8000), 2) if random.random() < 0.18 else 0,
                (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
            )
        )


async def _generate_reports(db, tenant_id: str):
    """生成3份演示报表"""
    report_types = ["daily", "weekly", "monthly"]
    insights_list = [
        '["建议增加抖音短视频投放预算", "百度关键词ROI下降，建议优化着陆页", "周末转化率提升20%"]',
        '["小学数学课程线索质量最高", "下午3-5点咨询转化率最佳", "建议增加百度品牌词预算"]',
        '["少儿编程课程ROI达到5.2", "建议优化移动端落地页", "周末投放效果优于工作日"]'
    ]
    
    for i, rtype in enumerate(report_types):
        await db.execute(
            """INSERT INTO mock_reports
               (id, tenant_id, report_type, date_range_start, date_range_end,
                status, insights, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                f"report_{secrets.token_hex(8)}",
                tenant_id,
                rtype,
                (datetime.now() - timedelta(days=(i+1)*10)).strftime("%Y-%m-%d"),
                datetime.now().strftime("%Y-%m-%d"),
                "ready",
                insights_list[i],
                datetime.now().isoformat()
            )
        )


async def _init_onboarding(db, tenant_id: str):
    """初始化引导状态"""
    await db.execute(
        """INSERT OR REPLACE INTO mock_onboarding
           (tenant_id, step1_done, step1_org_name, step1_industry)
           VALUES (?, ?, ?, ?)""",
        (tenant_id, 0, DEMO_CONFIG["org_name"], DEMO_CONFIG["industry"])
    )


async def _generate_attribution_rules(db, tenant_id: str):
    """生成归因规则"""
    rules = [
        {"name": "抖音咨询归因", "platform": "juliang", "keywords": '["咨询", "开口", "留资"]'},
        {"name": "百度搜索归因", "platform": "baidu", "keywords": '["报名", "咨询", "价格"]'},
        {"name": "微信社群归因", "platform": "wechat", "keywords": '["微课", "资料", "体验课"]'},
    ]
    
    for rule in rules:
        await db.execute(
            """INSERT INTO mock_attribution_rules
               (id, tenant_id, name, platform, keywords, priority, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                f"attr_{secrets.token_hex(8)}",
                tenant_id,
                rule["name"],
                rule["platform"],
                rule["keywords"],
                random.randint(1, 10),
                datetime.now().isoformat()
            )
        )

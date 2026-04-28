# EduAdCRM-MVP 技术方案文档

> **项目代号**：EduAdCRM-MVP  
> **文档版本**：v1.0  
> **生成日期**：2026-04-27  
> **适用范围**：教育行业广告×CRM数据平台，MVP 阶段  

---

## 一、原始技术栈问题分析与调整说明

### 1.1 原方案不合理之处

| 原方案 | 问题 | 调整方向 |
|--------|------|----------|
| Laravel 10 + PHP 8.2 | 用户要求后端优先 Python | 替换为 Python FastAPI |
| Livewire 3 + FluxUI | 服务端渲染，无法支持 App / 小程序多端复用 | 替换为前后端分离，React/Vue + Taro 小程序 |
| Laravel Queue（数据库驱动）| 数据库队列在大文件处理场景不稳定，高并发时易阻塞 | 替换为 Celery + Redis |
| Playwright 截图测试 sh 脚本 | 硬编码路径，不可移植，不属于业务需求 | 移除该约束，改为 pytest + 标准化 CI |
| 交付形式"排除移动 App" | 与前端多端适配要求冲突 | 架构设计支持 Web / App / 小程序三端 |
| ApexCharts（Livewire绑定）| 依赖 Livewire 响应式，脱离后端渲染后无优势 | 改用 ECharts（生态更强，小程序有官方版本） |

---

## 二、系统架构总览

### 2.1 架构风格

采用 **前后端分离 + API 驱动** 的单体分层架构（Modular Monolith）。

- **MVP 阶段不拆微服务**：团队小、边界未稳定，过早拆分是架构宇航员陷阱
- **模块边界清晰**：Auth / CRM / AdAccount / Analytics / Report 五个模块内聚，接口契约稳定后可按需独立部署
- **API First**：后端只提供 RESTful JSON API，三端（Web / App / 小程序）共用同一套接口

### 2.2 整体分层图

```
┌─────────────────────────────────────────────────────────────┐
│                        客户端层                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  Web (PC/H5) │  │  Mobile App  │  │  微信小程序       │   │
│  │  React + Ant │  │  React Native│  │  Taro (React)    │   │
│  │  Design Pro  │  │  (可选Phase2)│  │                  │   │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘   │
└─────────┼─────────────────┼───────────────────┼─────────────┘
          │                 │                   │
          └─────────────────┼───────────────────┘
                            │  HTTPS / REST API + JWT
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                       API 网关层                              │
│              Nginx (反向代理 + SSL 终止 + 限流)               │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      后端应用层                               │
│                  Python FastAPI (Uvicorn)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │   Auth   │ │   CRM    │ │ AdAccount│ │  Analytics   │   │
│  │  模块    │ │  模块    │ │   模块   │ │    模块      │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
│  ┌──────────┐ ┌────────────────────────────────────────┐    │
│  │  Report  │ │         任务调度 (APScheduler)          │    │
│  │  模块    │ │   每日广告数据拉取 / 月报自动生成         │    │
│  └──────────┘ └────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
┌─────────────┐  ┌──────────────┐  ┌──────────────┐
│  MySQL 8.0  │  │    Redis     │  │  对象存储     │
│  (主数据库) │  │  (缓存+队列) │  │  COS/MinIO   │
│             │  │  Celery队列  │  │  Excel文件    │
└─────────────┘  └──────────────┘  └──────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                                 ▼
┌──────────────────┐              ┌──────────────────┐
│  Celery Worker   │              │   外部广告 API    │
│  (异步任务处理)  │              │  巨量引擎 / 百度  │
│  - Excel解析      │              │  营销 API        │
│  - 广告数据同步   │              └──────────────────┘
│  - 报表生成       │
└──────────────────┘
```

---

## 三、技术栈选型

### 3.1 后端

| 组件 | 选型 | 版本 | 选型理由 |
|------|------|------|----------|
| Web 框架 | **FastAPI** | 0.111+ | 原生异步、自动生成 OpenAPI 文档、性能优、Python 生态最佳 REST 选择 |
| ASGI 服务器 | **Uvicorn** | 0.29+ | FastAPI 官方推荐，生产环境配合 Gunicorn 多进程 |
| ORM | **SQLAlchemy 2.x** | 2.0+ | 成熟稳定，支持异步，迁移工具 Alembic 完善 |
| 数据库迁移 | **Alembic** | - | 与 SQLAlchemy 原生集成 |
| 异步任务队列 | **Celery + Redis** | Celery 5.x | 替代数据库队列驱动，稳定可靠，支持定时任务（Celery Beat） |
| 缓存 | **Redis** | 7.x | 接口缓存、Token 黑名单、Celery Broker 三用合一 |
| Excel 解析 | **openpyxl + pandas** | - | Python 原生方案，5万行 CSV/Excel 处理稳定 |
| 认证 | **python-jose + passlib** | - | JWT 生成与校验，bcrypt 密码哈希 |
| HTTP 客户端 | **httpx** | - | 异步 HTTP，对接巨量引擎/百度营销 API |
| 邮件 | **FastAPI-Mail** | - | 异步邮件发送，支持 SMTP |
| 报表生成 | **openpyxl** | - | Excel 报表；PDF 用 **WeasyPrint** |
| 定时任务 | **Celery Beat** | - | 广告数据每日自动拉取、月报生成 |
| 日志 | **structlog** | - | 结构化日志，便于后续接入 ELK |
| 测试 | **pytest + httpx** | - | API 集成测试 |

### 3.2 前端

| 场景 | 选型 | 选型理由 |
|------|------|----------|
| **Web PC / H5 响应式** | **React 18 + Ant Design Pro 6** | 成熟中后台方案，响应式布局，图表生态完整 |
| **微信小程序** | **Taro 4（React 语法）** | 一套 React 代码编译至小程序，与 Web 端共享业务逻辑和组件 |
| **移动 App（Phase 2）** | **React Native（Expo）** | 与 Web/小程序共享部分逻辑，MVP 阶段可暂缓 |
| **图表** | **ECharts（Apache）+ echarts-for-react** | Web 端用 echarts-for-react；小程序用官方 ec-canvas；功能全面，教育行业折线/柱状/漏斗图全覆盖 |
| **状态管理** | **Zustand** | 轻量，比 Redux 简单，适合 MVP 快速开发 |
| **请求库** | **Axios + React Query** | Axios 统一封装 API 请求，React Query 处理缓存和加载态 |
| **样式** | **Tailwind CSS + Ant Design** | Ant Design 提供组件，Tailwind 处理定制布局 |
| **构建工具** | **Vite** | 开发体验快，打包效率高 |

### 3.3 数据库

| 组件 | 选型 | 说明 |
|------|------|------|
| 主数据库 | **MySQL 8.0** | 与现有宝塔环境一致，保留原方案 |
| 缓存/队列 | **Redis 7.x** | Celery broker + API 缓存 + Session |
| 文件存储 | **腾讯云 COS / 本地 MinIO** | Excel 上传文件持久化，不占数据库 |

### 3.4 基础设施

| 组件 | 选型 | 说明 |
|------|------|------|
| 反向代理 | **Nginx** | 与现有宝塔环境一致 |
| 容器化 | **Docker + docker-compose** | 开发/生产环境一致性，宝塔支持 Docker |
| 进程管理 | **Supervisor** | 管理 Uvicorn / Celery Worker / Celery Beat 进程 |
| SSL | **Let's Encrypt（宝塔一键）** | HTTPS 必须，微信小程序强制要求 |

---

## 四、多端适配架构设计

### 4.1 为什么能"一套 API 支撑三端"

```
后端 FastAPI
     │
     │  统一 REST API（JSON）
     │  Bearer Token 认证（JWT）
     │
  ┌──┴──────────────────────┐
  │                          │
  ▼                          ▼
Web 端（React）          小程序端（Taro）
Ant Design Pro           Taro + Vant Weapp
echarts-for-react        ec-canvas (ECharts)
React Query              网络请求封装
                              │
                              ▼
                         微信登录（openid）
                         → 后端换取 JWT
                         → 统一认证体系
```

### 4.2 微信小程序特殊处理

| 问题 | 处理方式 |
|------|----------|
| 微信登录 | 小程序端调用 `wx.login()` 获取 code → 发送至后端 → 后端调用微信 API 换取 openid → 返回 JWT |
| 文件上传 | 小程序使用 `wx.uploadFile()` → 后端接收后存 COS/MinIO → 与 Web 端相同的异步处理逻辑 |
| HTTPS 要求 | 微信小程序强制 HTTPS，需配置合法域名和 SSL 证书 |
| 图表适配 | 使用 ECharts 官方小程序版 `ec-canvas`，与 Web 端图表配置保持一致 |
| 数据展示 | 小程序主要承载"仪表盘查看"场景，Excel 上传等操作保留在 Web 端 |

### 4.3 Taro 代码共享策略

```
src/
├── api/           # 100% 共享：API 请求封装
├── store/         # 100% 共享：Zustand 状态
├── utils/         # 100% 共享：工具函数（日期/金额格式化）
├── components/    # 70% 共享：纯逻辑组件
│   ├── common/    # 完全共享：数据卡片、加载态
│   └── charts/    # 条件编译：Web 用 echarts-for-react，小程序用 ec-canvas
├── pages/         # 30% 共享：页面布局差异较大
│   ├── dashboard/ # 仪表盘（两端都有）
│   ├── crm/       # CRM 管理（主要 Web 端）
│   └── report/    # 报表查看（两端都有）
└── platforms/
    ├── web/       # Web 专属：布局、导航
    └── weapp/     # 小程序专属：TabBar、授权
```

---

## 五、数据库设计（核心表）

### 5.1 多租户设计原则

MVP 阶段采用 **共享数据库 + 行级隔离**（shared database, separate rows）：
- 所有核心表含 `tenant_id` 字段
- 所有查询通过 SQLAlchemy 中间件自动注入 `WHERE tenant_id = ?` 过滤
- 简单、低成本，满足 MVP 验证阶段需求

### 5.2 核心数据表

```sql
-- 租户表
tenants (id, name, industry_sub_type, main_product, created_at)

-- 用户表
users (id, tenant_id, email, password_hash, role, is_active, created_at)

-- 广告账户表
ad_accounts (
  id, tenant_id, platform ENUM('juliang','baidu'),
  account_id, account_name, access_token, refresh_token,
  token_expires_at, balance, status, created_at
)

-- 广告每日数据
ad_daily_stats (
  id, tenant_id, ad_account_id, platform,
  date, campaign_id, campaign_name, adgroup_id, adgroup_name,
  spend, impressions, clicks, form_submissions,
  cost_per_click, cost_per_form, created_at
)

-- CRM 线索批次
crm_import_batches (
  id, tenant_id, filename, file_path, total_rows,
  success_rows, skip_rows, fail_rows, status, created_at
)

-- CRM 线索明细
crm_leads (
  id, tenant_id, batch_id,
  name, phone_hash(sha256脱敏存储), source_channel,
  course_name, deal_status ENUM('deal','no_deal','following'),
  deal_amount, deal_date, raw_source_value, created_at
)

-- 渠道归因规则
attribution_rules (
  id, tenant_id, platform ENUM('juliang','baidu','other'),
  keywords JSON,  -- ["抖音","douyin","tiktok"]
  created_at
)

-- 操作日志
audit_logs (
  id, tenant_id, user_id, action, resource_type, resource_id,
  detail JSON, ip_address, created_at
)
```

---

## 六、后端模块设计（FastAPI）

### 6.1 项目结构

```
backend/
├── app/
│   ├── main.py                 # FastAPI 入口，注册路由
│   ├── core/
│   │   ├── config.py           # 配置（pydantic-settings，env 优先）
│   │   ├── database.py         # SQLAlchemy engine & session
│   │   ├── security.py         # JWT 生成/验证
│   │   ├── tenant.py           # 多租户中间件（自动注入 tenant_id）
│   │   └── exceptions.py       # 统一错误处理
│   ├── models/                 # SQLAlchemy ORM 模型
│   │   ├── user.py
│   │   ├── ad_account.py
│   │   ├── crm_lead.py
│   │   └── ...
│   ├── schemas/                # Pydantic 请求/响应模型
│   │   ├── auth.py
│   │   ├── crm.py
│   │   └── analytics.py
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py         # 注册/登录/刷新Token
│   │       ├── crm.py          # Excel上传/线索管理
│   │       ├── ad_accounts.py  # 广告账户OAuth/管理
│   │       ├── analytics.py    # ROI仪表盘/交叉分析
│   │       ├── reports.py      # 报表生成/下载
│   │       └── settings.py     # 归因规则/账户设置
│   ├── services/
│   │   ├── juliang_service.py  # 巨量引擎 API 封装
│   │   ├── baidu_service.py    # 百度营销 API 封装
│   │   ├── crm_importer.py     # Excel解析+字段映射
│   │   ├── roi_calculator.py   # ROI 计算逻辑
│   │   ├── attribution.py      # 线索归因引擎
│   │   └── report_generator.py # Excel/PDF 报表生成
│   ├── tasks/                  # Celery 异步任务
│   │   ├── celery_app.py       # Celery 初始化
│   │   ├── import_tasks.py     # Excel 异步导入
│   │   ├── sync_ad_tasks.py    # 广告数据定时同步
│   │   └── report_tasks.py     # 月报生成任务
│   └── utils/
│       ├── email.py
│       └── file_storage.py     # COS/MinIO 封装
├── alembic/                    # 数据库迁移
├── tests/                      # pytest 测试
├── requirements.txt
├── pyproject.toml
├── Dockerfile
└── docker-compose.yml
```

### 6.2 核心 API 接口清单

#### Auth 模块
```
POST /api/v1/auth/register          # 邮箱注册
POST /api/v1/auth/login             # 登录，返回 access_token + refresh_token
POST /api/v1/auth/refresh           # 刷新 Token
POST /api/v1/auth/logout            # 登出（Redis 黑名单）
POST /api/v1/auth/forgot-password   # 忘记密码
POST /api/v1/auth/reset-password    # 重置密码
POST /api/v1/auth/wx-login          # 微信小程序登录（code换JWT）
GET  /api/v1/auth/profile           # 当前用户信息
```

#### CRM 模块
```
POST /api/v1/crm/upload             # 上传 Excel/CSV 文件（触发异步任务）
GET  /api/v1/crm/upload/{task_id}   # 查询上传任务进度
POST /api/v1/crm/upload/{batch_id}/confirm  # 确认字段映射，开始导入
GET  /api/v1/crm/leads              # 线索列表（分页+筛选）
PATCH /api/v1/crm/leads/{id}        # 更新线索状态
DELETE /api/v1/crm/batches/{id}     # 删除整批导入记录
GET  /api/v1/crm/batches            # 导入批次列表
```

#### 广告账户模块
```
GET  /api/v1/ad/accounts            # 广告账户列表
GET  /api/v1/ad/juliang/oauth-url   # 获取巨量引擎授权 URL
GET  /api/v1/ad/juliang/callback    # OAuth 回调处理
GET  /api/v1/ad/baidu/oauth-url     # 获取百度营销授权 URL
GET  /api/v1/ad/baidu/callback      # OAuth 回调处理
DELETE /api/v1/ad/accounts/{id}     # 断开广告账户
POST /api/v1/ad/accounts/{id}/sync  # 手动触发数据同步
```

#### Analytics 模块
```
GET  /api/v1/analytics/dashboard    # ROI 仪表盘核心指标
GET  /api/v1/analytics/trend        # 近N天花费 vs 线索趋势
GET  /api/v1/analytics/channel-compare   # 渠道对比（抖音 vs 百度）
GET  /api/v1/analytics/cross-table  # 广告计划×课程交叉分析
GET  /api/v1/analytics/cross-table/export  # 导出 CSV
```

#### Reports 模块
```
POST /api/v1/reports/generate       # 手动生成报表（指定时间范围）
GET  /api/v1/reports                # 报表列表
GET  /api/v1/reports/{id}/download  # 下载 Excel/PDF
```

---

## 七、异步任务设计（Celery）

### 7.1 任务清单

| 任务名 | 触发方式 | 说明 |
|--------|----------|------|
| `process_crm_import` | 用户上传后异步触发 | 解析 Excel/CSV，去重，写入 DB |
| `sync_ad_data_juliang` | Celery Beat 每日 02:00 | 拉取巨量引擎昨日广告数据 |
| `sync_ad_data_baidu` | Celery Beat 每日 02:30 | 拉取百度昨日广告数据 |
| `generate_monthly_report` | Celery Beat 每月1日 08:00 | 生成上月 ROI 月报，发送邮件 |
| `send_sync_failure_alert` | 任务失败后触发 | 发送失败通知邮件给用户 |

### 7.2 Excel 导入流程

```
用户上传文件
    │
    ▼
FastAPI 接收 → 存入 COS/MinIO → 返回 task_id
    │
    ▼ (异步)
Celery Worker
    ├── 读取文件（openpyxl / pandas）
    ├── 解析字段映射
    ├── 去重检查（按 phone_hash）
    ├── 批量写入 DB（每500行一批）
    └── 更新任务状态（Redis 存储进度）
    │
    ▼
前端轮询 /api/v1/crm/upload/{task_id}
    └── 返回进度百分比 + 状态 + 汇总结果
```

---

## 八、前端架构设计

### 8.1 Web 端（React + Ant Design Pro）

```
frontend-web/
├── src/
│   ├── api/             # Axios 封装 + API 接口定义
│   ├── components/      # 共用组件
│   │   ├── RoiCard/     # 指标卡片
│   │   ├── TrendChart/  # ECharts 折线图封装
│   │   └── ChannelBar/  # 渠道对比柱状图
│   ├── pages/
│   │   ├── login/
│   │   ├── onboarding/  # 引导配置
│   │   ├── dashboard/   # ROI 仪表盘
│   │   ├── crm/         # CRM 导入+管理
│   │   ├── ad-accounts/ # 广告账户管理
│   │   ├── analytics/   # 交叉分析
│   │   ├── reports/     # 报表
│   │   └── settings/    # 归因规则设置
│   ├── store/           # Zustand 状态
│   ├── hooks/           # 自定义 hooks
│   └── utils/           # 工具函数
├── package.json
└── vite.config.ts
```

### 8.2 微信小程序端（Taro）

```
frontend-weapp/
├── src/
│   ├── api/             # 与 Web 端共享的 API 层（条件编译适配wx.request）
│   ├── pages/
│   │   ├── index/       # 首页（TabBar）
│   │   ├── dashboard/   # ROI 仪表盘（主要功能）
│   │   ├── crm/         # 线索列表（只读为主）
│   │   └── profile/     # 我的/账户
│   ├── components/
│   │   ├── EchartsWX/   # ec-canvas 封装
│   │   └── MetricCard/  # 指标卡片
│   └── app.config.ts    # 小程序配置（页面路由、TabBar）
├── project.config.json
└── package.json
```

---

## 九、部署架构

### 9.1 生产环境部署（宝塔 + Docker）

```
服务器（云主机，推荐 4C8G 起步）
├── Nginx（宝塔管理）
│   ├── 反向代理 → FastAPI (8000端口)
│   ├── 静态文件 → Web 前端 dist/
│   └── SSL 证书（Let's Encrypt，宝塔一键申请）
│
├── Docker Compose 管理以下服务：
│   ├── app（FastAPI + Uvicorn，Gunicorn多进程）
│   ├── celery-worker（Celery 任务处理）
│   ├── celery-beat（定时任务调度）
│   ├── redis（7.x）
│   └── flower（Celery 监控，可选）
│
├── MySQL 8.0（宝塔直接安装管理）
└── MinIO（对象存储，或直接用腾讯云COS）
```

### 9.2 docker-compose.yml（关键配置）

```yaml
version: '3.9'
services:
  app:
    build: .
    command: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
    environment:
      - DATABASE_URL=mysql+aiomysql://user:pass@host:3306/eduadcrm
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    restart: always

  celery-worker:
    build: .
    command: celery -A app.tasks.celery_app worker --loglevel=info -c 4
    depends_on:
      - redis
    restart: always

  celery-beat:
    build: .
    command: celery -A app.tasks.celery_app beat --loglevel=info
    depends_on:
      - redis
    restart: always

  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

### 9.3 微信小程序发布

```
1. 开发环境：Taro dev --type weapp
2. 打包：Taro build --type weapp
3. 上传至微信开发者工具
4. 后台配置合法域名（指向服务器域名）
5. 提审发布
```

---

## 十、安全设计

| 安全点 | 方案 |
|--------|------|
| 认证 | JWT（access token 2h，refresh token 7d），Redis 维护黑名单 |
| 多租户隔离 | 中间件层强制注入 tenant_id，禁止跨租户查询 |
| 敏感数据 | 手机号 SHA-256 哈希存储（去重用），不存明文 |
| OAuth Token | 广告平台 access_token AES-256 加密存储 |
| API 限流 | Nginx 层限制每 IP 每分钟请求数 |
| 文件上传 | 限制类型（xlsx/csv）、大小（最大 10MB），病毒扫描（可选） |
| HTTPS | 全站强制 HTTPS，小程序必须 |
| 操作日志 | 所有数据变更记录 audit_logs |
| SQL 注入 | SQLAlchemy ORM 参数化查询，禁止裸 SQL |

---

## 十一、Sprint 计划（调整后）

### Sprint 1（第1-2周）：跑通核心闭环

| 任务 | 技术实现 | 工期 |
|------|----------|------|
| A1 用户注册/登录 | FastAPI JWT 认证，邮件验证 | 4h |
| B1 Excel上传+字段映射 | 文件上传API + Celery + pandas解析 | 6h |
| C1 抖音广告账户OAuth | httpx + 巨量引擎 OAuth 2.0 | 8h |
| D1 ROI仪表盘基础版 | React + ECharts + 数据聚合API | 10h |

**Sprint 1 目标**：Web 端可注册、上传 Excel、绑定抖音账户、查看第一张 ROI 图表

### Sprint 2（第3-4周）：完整 MVP

| 任务 | 技术实现 | 工期 |
|------|----------|------|
| C2 百度广告账户OAuth | httpx + 百度 OAuth 2.0 | 6h |
| C3 广告数据定时拉取 | Celery Beat + 定时任务 | 8h |
| D2 广告×课程交叉分析 | 数据关联查询 + ECharts | 8h |
| D3 线索匹配引擎 | 归因规则配置 + 关联逻辑 | 5h |
| A2 引导配置 | React 步骤向导组件 | 3h |
| B2 CRM管理页 | 列表+筛选+状态更新 | 4h |
| **小程序 MVP** | Taro 仪表盘+线索查看 | 8h |

### Sprint 3（第5-6周）：验证与打磨

| 任务 | 说明 |
|------|------|
| E1 月报自动生成 | Celery Beat + openpyxl/WeasyPrint |
| F1-F3 系统设置页 | 账户管理、归因规则、订阅页 |
| 产品打磨 & Bug 修复 | - |
| 邀请 10 家教育机构内测 | - |

---

## 十二、质量保障

### 12.1 测试策略

```
tests/
├── unit/
│   ├── test_roi_calculator.py    # ROI 计算逻辑单元测试
│   ├── test_attribution.py       # 归因规则匹配测试
│   └── test_crm_importer.py      # Excel 解析测试
└── integration/
    ├── test_auth_api.py          # 认证 API 集成测试
    ├── test_crm_api.py           # CRM 上传/查询 API 测试
    └── test_analytics_api.py     # ROI 仪表盘 API 测试
```

运行：`pytest tests/ -v --cov=app`

### 12.2 非功能要求

| 指标 | 目标 | 实现方式 |
|------|------|----------|
| Excel 导入（5万行）| ≤ 10秒 | Celery 异步 + pandas 批量写入 |
| 仪表盘首屏响应 | ≤ 1秒 | Redis 缓存聚合结果（5分钟 TTL） |
| 广告数据同步失败 | 必须通知 | Celery 任务失败回调 → 邮件告警 |
| 数据操作审计 | 全覆盖 | FastAPI 中间件自动记录 audit_logs |
| 移动响应式 | Web + 小程序 | Ant Design 响应式栅格 + Taro 适配 |

---

## 十三、技术债务与演进路径

### MVP 阶段有意接受的技术债

| 债务 | 说明 | 解决时机 |
|------|------|----------|
| 共享数据库多租户 | 行级隔离，未物理分库 | 用户 > 100 家时考虑 Schema 隔离 |
| 无点击归因 | 基于渠道字段软匹配，非精准归因 | Phase 2 加 UTM 参数追踪 |
| 小程序功能阉割 | 主要只做查看，上传在 Web | Phase 2 补全小程序上传能力 |
| 无监控告警 | 仅日志 + 邮件通知 | 接入 Sentry / Prometheus |
| React Native App | MVP 阶段只有 Web + 小程序 | Phase 2 按需开发 |

### Phase 2 演进方向

```
MVP（Modular Monolith）
    │
    ▼ 当租户 > 100，流量出现瓶颈
按需拆分高频模块：
    ├── Analytics Service（独立服务，读密集）
    ├── Ad Sync Service（独立 Worker）
    └── 主应用保留 Auth + CRM + 设置
```

---

## 十四、关键风险与应对

| 风险 | 概率 | 影响 | 应对 |
|------|------|------|------|
| 巨量引擎/百度 API 审批延迟 | 高 | 阻塞 C 模块 | **第一天提交申请**；审批期间先用 Mock 数据开发仪表盘 |
| Excel 格式千变万化 | 中 | B1 字段映射复杂 | 字段映射做成交互式配置，不强求自动识别 |
| 小程序微信审核 | 低 | Sprint 2 延期 | 提前准备资质材料，避免功能违规 |
| 多租户数据泄露 | 低 | 严重 | 中间件强制隔离 + 集成测试验证 |

---

## 附录：依赖清单

### Python 核心依赖（requirements.txt）

```txt
fastapi==0.111.0
uvicorn[standard]==0.29.0
gunicorn==22.0.0
sqlalchemy==2.0.30
alembic==1.13.1
aiomysql==0.2.0
pydantic-settings==2.2.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
celery[redis]==5.4.0
redis==5.0.4
httpx==0.27.0
pandas==2.2.2
openpyxl==3.1.2
fastapi-mail==1.4.1
structlog==24.1.0
weasyprint==62.3
pytest==8.2.0
pytest-asyncio==0.23.7
httpx==0.27.0
```

### 前端核心依赖（package.json 摘要）

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "antd": "^5.17.0",
    "@ant-design/pro-components": "^2.7.0",
    "echarts": "^5.5.0",
    "echarts-for-react": "^3.0.2",
    "zustand": "^4.5.2",
    "axios": "^1.7.2",
    "@tanstack/react-query": "^5.40.0",
    "tailwindcss": "^3.4.4"
  },
  "devDependencies": {
    "vite": "^5.2.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.4.5"
  }
}
```

---

*技术方案文档版本：v1.0 | 生成日期：2026-04-27 | 基于 EduAdCRM-MVP 产品需求*

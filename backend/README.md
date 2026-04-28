# EduAdCRM Backend - 教育广告CRM平台后端

## 技术栈

- **Web 框架**: FastAPI 0.111+
- **数据库**: MySQL 8.0 + SQLAlchemy 2.x (异步)
- **任务队列**: Celery 5.x + Redis
- **认证**: JWT (python-jose) + bcrypt

## 项目结构

```
backend/
├── app/
│   ├── api/v1/           # API 路由
│   ├── core/             # 核心配置、安全、数据库
│   ├── models/           # SQLAlchemy 模型
│   ├── schemas/          # Pydantic Schema
│   ├── services/         # 业务逻辑服务
│   ├── tasks/            # Celery 异步任务
│   └── utils/            # 工具函数
├── tests/                # 测试
├── pyproject.toml       # 项目配置
└── requirements.txt     # 依赖（备用）
```

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -e .
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
# 数据库
DATABASE_URL=mysql+aiomysql://user:pass@localhost:3306/eduadcrm

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key-change-in-production

# 巨量引擎 OAuth
JULIANG_APP_ID=your_app_id
JULIANG_APP_SECRET=your_app_secret
JULIANG_CALLBACK_URL=http://localhost:8000/api/v1/ad/juliang/callback

# 百度营销 OAuth
BAIDU_APP_ID=your_app_id
BAIDU_APP_SECRET=your_app_secret
```

### 3. 启动服务

```bash
# 启动 FastAPI (开发)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 启动 Celery Worker
celery -A app.tasks.celery_app worker --loglevel=info

# 启动 Celery Beat (定时任务)
celery -A app.tasks.celery_app beat --loglevel=info
```

## 核心 API

### 广告账户

- `GET /api/v1/ad/juliang/oauth-url` - 获取巨量引擎授权 URL
- `GET /api/v1/ad/juliang/callback` - OAuth 回调处理
- `GET /api/v1/ad/accounts` - 广告账户列表
- `POST /api/v1/ad/accounts/{id}/sync` - 手动同步广告数据
- `GET /api/v1/ad/sync-status` - 获取同步状态

## 开发说明

### 巨量引擎 OAuth 流程

1. 前端调用 `/api/v1/ad/juliang/oauth-url` 获取授权 URL
2. 跳转到授权页面，用户授权
3. 巨量引擎回调到 `/api/v1/ad/juliang/callback`
4. 后端换取 Token，存储账户信息，触发立即同步（7天数据）
5. 返回成功，前端跳转到引导下一步

### 数据同步策略

- **立即同步**: OAuth 绑定后立即拉取 7 天历史数据
- **定时同步**: Celery Beat 每日凌晨 2:00 拉取前 2 天数据
- **手动同步**: 用户可手动触发任意天数（1-90天）

## 文档

- API 文档: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
# EduAdCRM 前端

教育广告 CRM 平台前端应用，基于 React + Ant Design + TypeScript。

## 技术栈

- **框架**: React 18 + TypeScript
- **UI 组件库**: Ant Design 5 + Ant Design Pro Components
- **图表**: ECharts + echarts-for-react
- **状态管理**: Zustand
- **数据请求**: Axios + React Query
- **样式**: Tailwind CSS
- **构建工具**: Vite

## 项目结构

```
frontend-web/
├── src/
│   ├── api/              # API 接口封装
│   ├── components/       # 通用组件
│   │   ├── RoiCard/      # ROI 指标卡片
│   │   ├── TrendChart/   # 趋势图表
│   │   ├── ChannelBar/   # 渠道对比
│   │   ├── EmptyState/   # 空态组件
│   │   ├── DemoDataToggle/   # 演示数据切换
│   │   ├── OnboardingWizard/  # 引导向导
│   │   ├── SetupProgressCard/ # 进度卡片
│   │   ├── SmartFieldMapper/  # 智能字段映射
│   │   ├── AttributionConfirm/ # 归因确认
│   │   ├── ProgressOverlay/    # 导入进度
│   │   ├── InsightCard/       # 行动建议
│   │   ├── ContextLink/      # 上下文跳转
│   │   └── Layout/            # 布局组件
│   ├── pages/            # 页面组件
│   ├── store/            # Zustand 状态
│   ├── hooks/            # 自定义 Hooks
│   ├── utils/            # 工具函数
│   ├── types/            # TypeScript 类型定义
│   ├── App.tsx           # 主应用
│   └── main.tsx          # 入口文件
├── public/               # 静态资源
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## 快速开始

### 安装依赖

```bash
cd frontend-web
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:3000

### 构建生产版本

```bash
npm run build
```

## 核心功能

### 1. 演示数据系统
- 新用户可查看演示数据（星海教育示例）
- Header 右上角切换开关

### 2. 3 步引导向导
- Step 1: 填写机构信息
- Step 2: 绑定广告账户（巨量引擎/百度）
- Step 3: 导入 CRM 线索

### 3. ROI 仪表盘
- 核心指标卡片（花费、线索、CPE、ROI）
- 趋势图表
- 渠道对比图
- 分阶段空态引导

### 4. CRM 线索管理
- Excel/CSV 文件上传
- 智能字段映射
- 归因规则自动确认
- 导入进度展示

### 5. 广告账户管理
- 巨量引擎/百度 OAuth 绑定
- 账户状态展示
- 手动同步触发

### 6. 交叉分析
- 广告计划 × 课程交叉分析
- CSV 导出

### 7. 报表中心
- ROI 日/周/月报生成
- 行动建议卡片
- Excel/PDF 下载

### 8. 设置
- 归因规则管理
- 账户信息设置

## 环境变量

```bash
cp .env.example .env.local
```

| 变量 | 说明 | 默认值 |
|------|------|--------|
| VITE_API_BASE_URL | API 基础地址 | /api/v1 |

## 开发说明

### API 代理配置

开发环境下，Vite 已配置 API 代理，将 `/api` 请求转发到后端服务。

```ts
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
},
```

### API 接口

API 接口定义在 `src/api/index.ts`，与后端 FastAPI 路由对应：

- `/api/v1/auth/*` - 认证模块
- `/api/v1/demo/*` - 演示数据
- `/api/v1/onboarding/*` - 引导状态
- `/api/v1/ad/*` - 广告账户
- `/api/v1/crm/*` - CRM 线索
- `/api/v1/analytics/*` - 数据分析
- `/api/v1/reports/*` - 报表
- `/api/v1/settings/*` - 设置

### 状态管理

使用 Zustand 管理全局状态：

- `authStore` - 认证状态
- `demoStore` - 演示模式状态
- `onboardingStore` - 引导进度状态

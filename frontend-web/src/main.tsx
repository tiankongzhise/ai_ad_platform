/**
 * React 入口文件
 */
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import dayjs from 'dayjs';

import App from './App';
import './index.css';

// 配置 dayjs 中文
import 'dayjs/locale/zh-cn';
dayjs.locale('zh-cn');

// 创建 React Query 客户端
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 分钟
    },
  },
});

// Ant Design 配置
const antdConfig = {
  locale: zhCN,
  theme: {
    token: {
      colorPrimary: '#0ea5e9',
      borderRadius: 6,
    },
  },
};

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <ConfigProvider {...antdConfig}>
          <App />
        </ConfigProvider>
      </QueryClientProvider>
    </BrowserRouter>
  </React.StrictMode>
);

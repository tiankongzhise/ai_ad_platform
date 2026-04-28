/**
 * 主应用组件
 * 路由配置和页面渲染
 */
import React, { useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { useAuthStore, useOnboardingStore } from '@/store';
import { Layout } from '@/components';
import {
  LoginPage,
  DashboardPage,
  CRMPage,
  AdAccountsPage,
  AnalyticsPage,
  ReportsPage,
  SettingsPage,
  OnboardingPage,
} from '@/pages';

// 受保护的路由组件
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading, checkAuth } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    checkAuth();
  }, []);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, isLoading, navigate]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500">加载中...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
};

// 公共路由组件
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading, checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, []);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      // 检查是否完成引导
      const { fetchStatus, isCompleted } = useOnboardingStore.getState();
      fetchStatus().then(() => {
        const state = useOnboardingStore.getState();
        if (state.isCompleted) {
          window.location.href = '/dashboard';
        } else {
          window.location.href = '/onboarding';
        }
      });
    }
  }, [isAuthenticated, isLoading]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500">加载中...</p>
        </div>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

const App: React.FC = () => {
  return (
    <Routes>
      {/* 公共路由 */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        }
      />

      {/* 引导页面 */}
      <Route
        path="/onboarding"
        element={
          <ProtectedRoute>
            <OnboardingPage />
          </ProtectedRoute>
        }
      />

      {/* 受保护的路由 */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="crm" element={<CRMPage />} />
        <Route path="ad-accounts" element={<AdAccountsPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>

      {/* 404 重定向 */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

export default App;

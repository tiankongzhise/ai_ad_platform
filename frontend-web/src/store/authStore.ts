/**
 * 认证状态管理
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@/types';
import { authApi } from '@/api';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, tenantName: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  setUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (email: string, password: string) => {
        set({ isLoading: true });
        try {
          const response = await authApi.login({ email, password });
          const { access_token, refresh_token } = response.data;
          
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);

          // 获取用户信息
          const profileResponse = await authApi.getProfile();
          
          set({
            user: profileResponse.data,
            accessToken: access_token,
            refreshToken: refresh_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      register: async (email: string, password: string, tenantName: string) => {
        set({ isLoading: true });
        try {
          await authApi.register({ email, password, tenant_name: tenantName });
          // 注册成功后自动登录
          await get().login(email, password);
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      logout: async () => {
        try {
          await authApi.logout();
        } catch {
          // 即使失败也清除本地状态
        } finally {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          set({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,
          });
        }
      },

      checkAuth: async () => {
        const token = localStorage.getItem('access_token');
        if (!token) {
          set({ isAuthenticated: false });
          return;
        }

        set({ isLoading: true });
        try {
          const response = await authApi.getProfile();
          set({
            user: response.data,
            accessToken: token,
            refreshToken: localStorage.getItem('refresh_token'),
            isAuthenticated: true,
            isLoading: false,
          });
        } catch {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          set({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      },

      setUser: (user: User) => {
        set({ user });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

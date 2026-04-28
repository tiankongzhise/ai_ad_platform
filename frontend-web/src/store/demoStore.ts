/**
 * 演示数据状态管理
 * 控制演示模式与真实数据的切换
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { DemoDashboardResponse } from '@/types';
import { demoApi } from '@/api';

interface DemoState {
  // 是否为演示模式
  isDemoMode: boolean;
  // 演示数据缓存
  demoData: DemoDashboardResponse | null;
  // 是否正在加载演示数据
  isLoading: boolean;
  // 错误信息
  error: string | null;

  // Actions
  toggleDemoMode: () => void;
  enableDemoMode: () => void;
  disableDemoMode: () => void;
  fetchDemoData: () => Promise<void>;
  clearDemoData: () => void;
}

export const useDemoStore = create<DemoState>()(
  persist(
    (set, get) => ({
      isDemoMode: false,
      demoData: null,
      isLoading: false,
      error: null,

      toggleDemoMode: () => {
        const newMode = !get().isDemoMode;
        set({ isDemoMode: newMode });
        
        // 如果切换到演示模式且没有数据，则获取演示数据
        if (newMode && !get().demoData) {
          get().fetchDemoData();
        }
      },

      enableDemoMode: () => {
        set({ isDemoMode: true });
        if (!get().demoData) {
          get().fetchDemoData();
        }
      },

      disableDemoMode: () => {
        set({ isDemoMode: false });
      },

      fetchDemoData: async () => {
        set({ isLoading: true, error: null });
        try {
          const response = await demoApi.getDashboard();
          set({
            demoData: response.data,
            isLoading: false,
          });
        } catch (error) {
          set({
            error: '获取演示数据失败',
            isLoading: false,
          });
        }
      },

      clearDemoData: () => {
        set({
          demoData: null,
          isDemoMode: false,
          error: null,
        });
      },
    }),
    {
      name: 'demo-storage',
      partialize: (state) => ({
        isDemoMode: state.isDemoMode,
        demoData: state.demoData,
      }),
    }
  )
);

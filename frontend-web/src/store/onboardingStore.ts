/**
 * 引导状态管理
 * 跟踪用户的引导步骤进度
 */
import { create } from 'zustand';
import type { OnboardingStatus, OnboardingStep1, OnboardingStep2 } from '@/types';
import { onboardingApi } from '@/api';

interface OnboardingState {
  // 当前引导状态
  status: OnboardingStatus | null;
  // 是否正在加载
  isLoading: boolean;
  // 是否已完成引导
  isCompleted: boolean;
  // 当前步骤
  currentStep: 1 | 2 | 3;
  // 错误信息
  error: string | null;

  // Actions
  fetchStatus: () => Promise<void>;
  updateStep1: (data: OnboardingStep1) => Promise<void>;
  updateStep2: (data: OnboardingStep2) => Promise<void>;
  completeStep3: () => Promise<void>;
  completeOnboarding: () => Promise<void>;
  resetOnboarding: () => void;
}

export const useOnboardingStore = create<OnboardingState>((set, get) => ({
  status: null,
  isLoading: false,
  isCompleted: false,
  currentStep: 1,
  error: null,

  fetchStatus: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await onboardingApi.getStatus();
      const status = response.data;
      
      // 计算当前步骤
      let currentStep: 1 | 2 | 3 = 1;
      if (status.completed_at) {
        currentStep = 3;
      } else if (status.step2_ad_bound) {
        currentStep = 3;
      } else if (status.step1_org_info) {
        currentStep = 2;
      }

      set({
        status,
        isCompleted: !!status.completed_at,
        currentStep,
        isLoading: false,
      });
    } catch (error) {
      // 如果是 404，说明还没有引导记录，这是正常的
      if ((error as any).response?.status === 404) {
        set({
          status: null,
          isCompleted: false,
          currentStep: 1,
          isLoading: false,
        });
      } else {
        set({
          error: '获取引导状态失败',
          isLoading: false,
        });
      }
    }
  },

  updateStep1: async (data: OnboardingStep1) => {
    set({ isLoading: true, error: null });
    try {
      const response = await onboardingApi.updateStatus({ step1_org_info: data });
      set({
        status: response.data,
        currentStep: 2,
        isLoading: false,
      });
    } catch (error) {
      set({
        error: '保存机构信息失败',
        isLoading: false,
      });
      throw error;
    }
  },

  updateStep2: async (data: OnboardingStep2) => {
    set({ isLoading: true, error: null });
    try {
      const response = await onboardingApi.updateStatus({ step2_ad_bound: data });
      set({
        status: response.data,
        currentStep: 3,
        isLoading: false,
      });
    } catch (error) {
      set({
        error: '保存广告绑定失败',
        isLoading: false,
      });
      throw error;
    }
  },

  completeStep3: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await onboardingApi.updateStatus({ step3_crm_imported: true });
      set({
        status: response.data,
        currentStep: 3,
        isLoading: false,
      });
    } catch (error) {
      set({
        error: '保存CRM导入状态失败',
        isLoading: false,
      });
      throw error;
    }
  },

  completeOnboarding: async () => {
    set({ isLoading: true, error: null });
    try {
      await onboardingApi.complete();
      set({
        isCompleted: true,
        isLoading: false,
      });
    } catch (error) {
      set({
        error: '完成引导失败',
        isLoading: false,
      });
      throw error;
    }
  },

  resetOnboarding: () => {
    set({
      status: null,
      isCompleted: false,
      currentStep: 1,
      error: null,
    });
  },
}));

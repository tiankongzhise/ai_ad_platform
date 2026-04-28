/**
 * 引导配置页面
 * 3步引导独立页面
 */
import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { OnboardingWizard } from '@/components';
import { useOnboardingStore } from '@/store';

export const OnboardingPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const step = searchParams.get('step');
  const { fetchStatus, isCompleted } = useOnboardingStore();

  useEffect(() => {
    fetchStatus();
  }, []);

  // 如果引导已完成，跳转到仪表盘
  useEffect(() => {
    if (isCompleted) {
      navigate('/dashboard');
    }
  }, [isCompleted, navigate]);

  const handleComplete = () => {
    navigate('/dashboard');
  };

  const handleSkip = () => {
    navigate('/dashboard');
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center"
      style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <div className="w-full max-w-3xl mx-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-blue-500 mb-2">EduAdCRM</h1>
            <p className="text-gray-500">快速配置，开始使用</p>
          </div>

          <OnboardingWizard
            open={true}
            onComplete={handleComplete}
            onSkip={handleSkip}
          />
        </div>
      </div>
    </div>
  );
};

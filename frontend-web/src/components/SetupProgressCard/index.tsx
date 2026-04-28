/**
 * 设置进度卡片组件
 * 仪表盘底部固定进度展示
 */
import React from 'react';
import { Card, Progress, Button } from 'antd';
import { RightOutlined } from '@ant-design/icons';
import { useOnboardingStore } from '@/store';

interface SetupProgressCardProps {
  onContinue: () => void;
}

export const SetupProgressCard: React.FC<SetupProgressCardProps> = ({ onContinue }) => {
  const { status, currentStep, isCompleted } = useOnboardingStore();

  if (isCompleted || !status) {
    return null;
  }

  // 计算进度
  const getProgress = () => {
    if (status.step3_crm_imported) return 100;
    if (status.step2_ad_bound) return 66;
    if (status.step1_org_info) return 33;
    return 0;
  };

  // 获取下一步
  const getNextStep = () => {
    if (!status.step1_org_info) {
      return { text: '填写机构信息', path: '/onboarding?step=1' };
    }
    if (!status.step2_ad_bound) {
      return { text: '绑定广告账户', path: '/ad-accounts' };
    }
    if (!status.step3_crm_imported) {
      return { text: '导入 CRM 线索', path: '/crm' };
    }
    return null;
  };

  const nextStep = getNextStep();
  const progress = getProgress();

  return (
    <Card
      className="fixed bottom-4 left-1/2 -translate-x-1/2 shadow-lg"
      styles={{
        body: {
          padding: '16px 24px',
          borderRadius: '12px',
        }
      }}
      style={{
        maxWidth: '480px',
        width: 'calc(100% - 32px)',
        borderRadius: '12px',
      }}
    >
      <div className="flex items-center gap-4">
        <Progress
          type="circle"
          percent={progress}
          size={48}
          strokeColor="#0ea5e9"
          format={(percent) => (
            <span className="text-sm font-medium">{percent}%</span>
          )}
        />
        <div className="flex-1">
          <div className="text-sm text-gray-500 mb-1">完成基础配置，开启完整功能</div>
          <div className="text-base font-medium">
            {progress === 100
              ? '配置完成！'
              : nextStep
              ? `下一步：${nextStep.text}`
              : '进行中...'}
          </div>
        </div>
        {nextStep && (
          <Button
            type="primary"
            icon={<RightOutlined />}
            onClick={onContinue}
          >
            继续
          </Button>
        )}
      </div>
    </Card>
  );
};

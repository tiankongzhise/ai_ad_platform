/**
 * 空态组件
 * 分阶段展示不同场景的空态引导
 */
import React from 'react';
import { Button, Space } from 'antd';
import {
  ShopOutlined,
  CloudUploadOutlined,
  DatabaseOutlined,
  ArrowRightOutlined,
} from '@ant-design/icons';
import type { DashboardStatus } from '@/types';

interface EmptyStateProps {
  scenario: DashboardStatus;
  onAction: () => void;
  onViewDemo?: () => void;
  onSkip?: () => void;
}

const SCENARIOS: Record<DashboardStatus, {
  icon: React.ReactNode;
  title: string;
  description: string;
  actionText: string;
  secondaryAction?: { text: string; onClick: () => void };
}> = {
  scenario_a: {
    icon: <ShopOutlined className="text-4xl text-blue-400" />,
    title: '绑定广告账户',
    description: '连接您的抖音/百度广告账户，我们就能开始追踪广告效果和转化数据了。',
    actionText: '立即绑定',
    secondaryAction: {
      text: '先看看演示数据',
      onClick: () => {},
    },
  },
  scenario_b: {
    icon: <CloudUploadOutlined className="text-4xl text-blue-400" />,
    title: '数据同步中...',
    description: '正在从广告平台拉取历史数据，请稍候。通常需要 5-10 分钟。',
    actionText: '刷新状态',
  },
  scenario_c: {
    icon: <DatabaseOutlined className="text-4xl text-blue-400" />,
    title: '导入 CRM 线索',
    description: '有了广告数据，现在导入您的 CRM 线索，我们就能计算 ROI 和归因了。',
    actionText: '导入线索',
    secondaryAction: {
      text: '先看看演示数据',
      onClick: () => {},
    },
  },
  full_data: {
    icon: <DatabaseOutlined className="text-4xl text-green-400" />,
    title: '暂无数据',
    description: '当前时间段内没有数据，请尝试调整时间范围。',
    actionText: '调整筛选条件',
  },
};

export const EmptyState: React.FC<EmptyStateProps> = ({
  scenario,
  onAction,
  onViewDemo,
  onSkip,
}) => {
  const config = SCENARIOS[scenario];

  if (scenario === 'scenario_b') {
    // 同步中状态，显示加载动画
    return (
      <div className="empty-state">
        <div className="mb-6 animate-pulse">
          {config.icon}
        </div>
        <h3 className="text-xl font-medium text-gray-800 mb-2">{config.title}</h3>
        <p className="text-gray-500 mb-6 max-w-sm">{config.description}</p>
        <Space>
          <Button type="primary" onClick={onAction}>
            {config.actionText}
          </Button>
          {onSkip && (
            <Button onClick={onSkip}>
              跳过，稍后查看
            </Button>
          )}
        </Space>
      </div>
    );
  }

  return (
    <div className="empty-state">
      <div className="mb-6">
        {config.icon}
      </div>
      <h3 className="text-xl font-medium text-gray-800 mb-2">{config.title}</h3>
      <p className="text-gray-500 mb-6 max-w-sm">{config.description}</p>
      <Space direction="vertical" align="center" size={4}>
        <Button
          type="primary"
          size="large"
          icon={<ArrowRightOutlined />}
          onClick={onAction}
        >
          {config.actionText}
        </Button>
        {config.secondaryAction && (
          <Button
            type="link"
            onClick={onViewDemo}
          >
            {config.secondaryAction.text}
          </Button>
        )}
      </Space>
    </div>
  );
};

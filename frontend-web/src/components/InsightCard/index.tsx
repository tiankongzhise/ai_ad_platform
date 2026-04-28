/**
 * 行动建议卡片组件
 * 展示智能分析得出的行动建议
 */
import React from 'react';
import { Card, Tag, Button } from 'antd';
import {
  BulbOutlined,
  WarningOutlined,
  InfoCircleOutlined,
  ArrowRightOutlined,
} from '@ant-design/icons';
import type { InsightCard as InsightCardType } from '@/types';

interface InsightCardProps {
  insight: InsightCardType;
  onAction?: () => void;
}

const TYPE_CONFIG = {
  opportunity: {
    icon: <BulbOutlined className="text-yellow-500" />,
    color: '#fef3c7',
    borderColor: '#fbbf24',
    tagColor: 'gold',
  },
  warning: {
    icon: <WarningOutlined className="text-orange-500" />,
    color: '#ffedd5',
    borderColor: '#f97316',
    tagColor: 'orange',
  },
  info: {
    icon: <InfoCircleOutlined className="text-blue-500" />,
    color: '#dbeafe',
    borderColor: '#3b82f6',
    tagColor: 'blue',
  },
};

export const InsightCard: React.FC<InsightCardProps> = ({ insight, onAction }) => {
  const config = TYPE_CONFIG[insight.type];

  return (
    <Card
      className="h-full"
      styles={{
        body: {
          padding: '16px',
          backgroundColor: config.color,
          borderLeft: `4px solid ${config.borderColor}`,
          borderRadius: '8px',
        },
      }}
    >
      <div className="flex items-start gap-3">
        <div className="text-2xl">{config.icon}</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span className="font-medium text-base">{insight.title}</span>
            <Tag color={config.tagColor} className="text-xs">
              {insight.type === 'opportunity' ? '机会' : insight.type === 'warning' ? '预警' : '提示'}
            </Tag>
          </div>
          <p className="text-gray-600 text-sm mb-3 line-clamp-2">
            {insight.description}
          </p>
          {insight.action_text && insight.action_url && (
            <Button
              type="link"
              size="small"
              className="p-0 h-auto"
              onClick={onAction}
            >
              {insight.action_text}
              <ArrowRightOutlined className="ml-1" />
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
};

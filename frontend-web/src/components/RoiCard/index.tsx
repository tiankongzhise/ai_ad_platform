/**
 * ROI 指标卡片组件
 * 展示核心指标和趋势
 */
import React from 'react';
import { Card, Statistic, Tooltip } from 'antd';
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  QuestionCircleOutlined,
} from '@ant-design/icons';
import { formatTrend, formatCurrency, formatNumber } from '@/utils';

interface RoiCardProps {
  title: string;
  value: number;
  trend?: number;
  format?: 'currency' | 'number' | 'percent' | 'ratio';
  tooltip?: string;
  loading?: boolean;
  className?: string;
}

export const RoiCard: React.FC<RoiCardProps> = ({
  title,
  value,
  trend,
  format = 'number',
  tooltip,
  loading = false,
  className = '',
}) => {
  // 格式化数值
  const formatValue = () => {
    switch (format) {
      case 'currency':
        return formatCurrency(value);
      case 'percent':
        return `${(value * 100).toFixed(2)}%`;
      case 'ratio':
        return `${value.toFixed(2)}:1`;
      default:
        return formatNumber(value);
    }
  };

  // 格式化趋势
  const getTrendIcon = () => {
    if (trend === undefined || trend === 0) return null;
    return trend > 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />;
  };

  const getTrendColor = () => {
    if (trend === undefined || trend === 0) return 'gray';
    // 花费和CPL越低越好，线索和ROI越高越好
    const isPositive = title.includes('花费') || title.includes('CPL')
      ? trend < 0
      : trend > 0;
    return isPositive ? '#52c41a' : '#ff4d4f';
  };

  return (
    <Card
      className={`metric-card ${className}`}
      loading={loading}
      styles={{ body: { padding: '20px 24px' } }}
    >
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center gap-1 mb-2">
            <span className="text-gray-500 text-sm">{title}</span>
            {tooltip && (
              <Tooltip title={tooltip}>
                <QuestionCircleOutlined className="text-gray-400 text-xs" />
              </Tooltip>
            )}
          </div>
          <Statistic
            value={value}
            formatter={formatValue}
            valueStyle={{
              fontSize: '28px',
              fontWeight: 600,
              color: '#1a1a1a',
              lineHeight: 1.4,
            }}
          />
        </div>
        {trend !== undefined && (
          <div
            className="flex items-center gap-0.5 px-2 py-1 rounded text-xs font-medium"
            style={{
              color: getTrendColor(),
              backgroundColor: `${getTrendColor()}15`,
            }}
          >
            {getTrendIcon()}
            <span>{formatTrend(trend)}</span>
          </div>
        )}
      </div>
    </Card>
  );
};

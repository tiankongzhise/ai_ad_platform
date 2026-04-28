/**
 * 仪表盘页面
 * ROI 核心指标展示
 */
import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Spin, DatePicker, Space, Segmented } from 'antd';
import dayjs from 'dayjs';
import { useNavigate } from 'react-router-dom';
import {
  RoiCard,
  TrendChart,
  ChannelBar,
  EmptyState,
  SetupProgressCard,
} from '@/components';
import { useDemoStore, useOnboardingStore } from '@/store';
import { analyticsApi, demoApi } from '@/api';
import type { DashboardMetrics, TrendDataPoint, ChannelComparison, DashboardStatus } from '@/types';
import { formatCurrency, formatNumber } from '@/utils';

const { RangePicker } = DatePicker;

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { isDemoMode, demoData, fetchDemoData, enableDemoMode } = useDemoStore();
  const { isCompleted: onboardingCompleted, fetchStatus } = useOnboardingStore();

  // 数据状态
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [trends, setTrends] = useState<TrendDataPoint[]>([]);
  const [channels, setChannels] = useState<ChannelComparison[]>([]);
  const [dashboardStatus, setDashboardStatus] = useState<DashboardStatus | null>(null);
  
  // UI状态
  const [isLoading, setIsLoading] = useState(true);
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().subtract(30, 'day'),
    dayjs(),
  ]);
  const [timeRange, setTimeRange] = useState<number>(30);

  useEffect(() => {
    fetchData();
    if (!onboardingCompleted) {
      fetchStatus();
    }
  }, []);

  useEffect(() => {
    if (isDemoMode && !demoData) {
      fetchDemoData();
    }
  }, [isDemoMode]);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      // 获取仪表盘状态
      const statusRes = await analyticsApi.getDashboardStatus();
      setDashboardStatus(statusRes.data.status);

      // 如果有数据，获取完整数据
      if (statusRes.data.status === 'full_data' || statusRes.data.has_ad_data) {
        const [metricsRes, trendRes, channelRes] = await Promise.all([
          analyticsApi.getDashboard(),
          analyticsApi.getTrend({ days: timeRange }),
          analyticsApi.getChannelCompare(),
        ]);
        setMetrics(metricsRes.data);
        setTrends(trendRes.data);
        setChannels(channelRes.data);
      }
    } catch (error) {
      console.error('获取仪表盘数据失败', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTimeRangeChange = (value: number) => {
    setTimeRange(value);
    setDateRange([dayjs().subtract(value, 'day'), dayjs()]);
  };

  const handleAction = () => {
    // 根据状态跳转到相应页面
    switch (dashboardStatus) {
      case 'scenario_a':
        navigate('/ad-accounts');
        break;
      case 'scenario_c':
        navigate('/crm');
        break;
      default:
        fetchData();
    }
  };

  const handleViewDemo = () => {
    // 切换到演示模式
    enableDemoMode();
  };

  // 显示空态
  if (!isLoading && !isDemoMode && dashboardStatus && dashboardStatus !== 'full_data') {
    return (
      <div className="page-container">
        <div className="mb-6">
          <h1 className="text-2xl font-bold">数据概览</h1>
          <p className="text-gray-500">查看您的广告投放效果和 ROI</p>
        </div>
        <EmptyState
          scenario={dashboardStatus}
          onAction={handleAction}
          onViewDemo={handleViewDemo}
          onSkip={() => {}}
        />
      </div>
    );
  }

  // 使用演示数据
  const displayMetrics = isDemoMode && demoData ? demoData.metrics : metrics;
  const displayTrends = isDemoMode && demoData 
    ? demoData.trends.map(t => ({ date: t.date, spend: t.spend, leads: t.leads }))
    : trends;
  const displayChannels = isDemoMode && demoData
    ? demoData.channel_compare.map(c => ({
        platform: c.platform as any,
        spend: c.spend,
        leads: c.leads,
        cpl: c.spend / Math.max(c.leads, 1),
        roi: c.roi,
      }))
    : channels;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div className="page-container">
      {/* 页面头部 */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">数据概览</h1>
          <p className="text-gray-500">
            {isDemoMode ? `演示数据 - ${demoData?.org_name || '星海教育'}` : '查看您的广告投放效果和 ROI'}
          </p>
        </div>
        <Space>
          <Segmented<number>
            value={timeRange}
            onChange={handleTimeRangeChange}
            options={[
              { label: '7天', value: 7 },
              { label: '30天', value: 30 },
              { label: '90天', value: 90 },
            ]}
          />
          <RangePicker
            value={dateRange}
            onChange={(dates) => dates && setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs])}
          />
        </Space>
      </div>

      {/* 核心指标卡片 */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} sm={12} lg={6}>
          <RoiCard
            title="今日花费"
            value={displayMetrics?.total_spend || 0}
            trend={displayMetrics?.spend_trend}
            format="currency"
            tooltip="今日广告投放总花费"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <RoiCard
            title="累计线索"
            value={displayMetrics?.total_leads || 0}
            trend={displayMetrics?.leads_trend}
            format="number"
            tooltip="统计周期内的广告线索总数"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <RoiCard
            title="平均 CPE"
            value={displayMetrics?.cost_per_lead || 0}
            format="currency"
            tooltip="平均每个线索的获取成本"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <RoiCard
            title="投资回报率"
            value={displayMetrics?.roi || 0}
            format="ratio"
            tooltip="广告投入与线索价值的比值"
          />
        </Col>
      </Row>

      {/* 图表区域 */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} lg={16}>
          <TrendChart
            title="花费 vs 线索趋势"
            data={displayTrends}
            height={320}
          />
        </Col>
        <Col xs={24} lg={8}>
          <ChannelBar
            title="渠道对比"
            data={displayChannels}
            height={320}
          />
        </Col>
      </Row>

      {/* 引导进度卡片 */}
      {!onboardingCompleted && (
        <SetupProgressCard onContinue={() => navigate('/onboarding')} />
      )}
    </div>
  );
};

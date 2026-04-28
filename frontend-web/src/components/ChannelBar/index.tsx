/**
 * 渠道对比柱状图组件
 * 展示不同广告渠道的效果对比
 */
import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Spin } from 'antd';
import type { EChartsOption } from 'echarts';

interface ChannelBarProps {
  title?: string;
  data: Array<{
    platform: string;
    spend: number;
    leads: number;
    cpl: number;
    roi: number;
  }>;
  loading?: boolean;
  height?: number;
}

const PLATFORM_COLORS: Record<string, string> = {
  juliang: '#fe4c4c', // 抖音红
  baidu: '#2932e1',   // 百度蓝
};

export const ChannelBar: React.FC<ChannelBarProps> = ({
  title = '渠道对比',
  data,
  loading = false,
  height = 320,
}) => {
  const option: EChartsOption = useMemo(() => {
    const platforms = data.map((d) => {
      const names: Record<string, string> = {
        juliang: '巨量引擎（抖音）',
        baidu: '百度营销',
      };
      return names[d.platform] || d.platform;
    });

    return {
      title: {
        text: title,
        textStyle: {
          fontSize: 16,
          fontWeight: 500,
          color: '#1a1a1a',
        },
        left: 0,
        top: 0,
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow',
        },
        formatter: (params: any) => {
          if (!Array.isArray(params) || params.length === 0) return '';
          const index = params[0].dataIndex;
          const item = data[index];
          return `
            <div style="font-weight:500;margin-bottom:8px">${item.platform}</div>
            <div>花费: ¥${item.spend.toLocaleString()}</div>
            <div>线索: ${item.leads}</div>
            <div>CPL: ¥${item.cpl.toFixed(2)}</div>
            <div>ROI: ${item.roi.toFixed(2)}:1</div>
          `;
        },
      },
      legend: {
        data: ['花费', '线索'],
        right: 0,
        top: 0,
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '50px',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: platforms,
        axisLine: {
          lineStyle: {
            color: '#e8e8e8',
          },
        },
        axisLabel: {
          color: '#666',
          interval: 0,
          rotate: 0,
        },
      },
      yAxis: [
        {
          type: 'value',
          name: '花费(¥)',
          axisLabel: {
            color: '#666',
            formatter: (value: number) => {
              if (value >= 10000) return `${value / 10000}万`;
              return value.toString();
            },
          },
          splitLine: {
            lineStyle: {
              color: '#f0f0f0',
            },
          },
        },
        {
          type: 'value',
          name: '线索',
          position: 'right',
          axisLabel: {
            color: '#666',
          },
          splitLine: {
            show: false,
          },
        },
      ],
      series: [
        {
          name: '花费',
          type: 'bar',
          barWidth: '35%',
          data: data.map((d) => ({
            value: d.spend,
            itemStyle: {
              color: PLATFORM_COLORS[d.platform] || '#0ea5e9',
            },
          })),
          label: {
            show: true,
            position: 'top',
            formatter: (params: any) => {
              const value = params.value;
              if (value >= 10000) return `${(value / 10000).toFixed(1)}万`;
              return value.toString();
            },
            color: '#666',
            fontSize: 11,
          },
        },
        {
          name: '线索',
          type: 'bar',
          barWidth: '35%',
          yAxisIndex: 1,
          data: data.map((d) => d.leads),
          itemStyle: {
            color: '#10b981',
          },
          label: {
            show: true,
            position: 'top',
            formatter: (params: any) => params.value.toString(),
            color: '#666',
            fontSize: 11,
          },
        },
      ],
    };
  }, [data, title]);

  if (loading) {
    return (
      <Card className="card" styles={{ body: { height } }}>
        <div className="flex items-center justify-center h-full">
          <Spin />
        </div>
      </Card>
    );
  }

  return (
    <Card className="card" styles={{ body: { padding: '16px 20px' } }}>
      <ReactECharts
        option={option}
        style={{ height }}
        opts={{ renderer: 'canvas' }}
      />
    </Card>
  );
};

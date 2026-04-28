/**
 * 趋势图表组件
 * 基于 ECharts 的折线图封装
 */
import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Spin } from 'antd';
import type { EChartsOption } from 'echarts';
import dayjs from 'dayjs';

interface TrendChartProps {
  title?: string;
  data: Array<{
    date: string;
    spend?: number;
    leads?: number;
  }>;
  loading?: boolean;
  height?: number;
  showSpend?: boolean;
  showLeads?: boolean;
}

export const TrendChart: React.FC<TrendChartProps> = ({
  title = '趋势分析',
  data,
  loading = false,
  height = 320,
  showSpend = true,
  showLeads = true,
}) => {
  const option: EChartsOption = useMemo(() => {
    const dates = data.map((d) => dayjs(d.date).format('MM-DD'));
    const spendData = data.map((d) => d.spend || 0);
    const leadsData = data.map((d) => d.leads || 0);

    const series: any[] = [];

    if (showSpend) {
      series.push({
        name: '花费',
        type: 'line',
        yAxisIndex: 0,
        data: spendData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: {
          width: 2,
          color: '#0ea5e9',
        },
        itemStyle: {
          color: '#0ea5e9',
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(14, 165, 233, 0.3)' },
              { offset: 1, color: 'rgba(14, 165, 233, 0.05)' },
            ],
          },
        },
      });
    }

    if (showLeads) {
      series.push({
        name: '线索',
        type: 'line',
        yAxisIndex: 1,
        data: leadsData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: {
          width: 2,
          color: '#10b981',
        },
        itemStyle: {
          color: '#10b981',
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(16, 185, 129, 0.3)' },
              { offset: 1, color: 'rgba(16, 185, 129, 0.05)' },
            ],
          },
        },
      });
    }

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
          type: 'cross',
          label: {
            backgroundColor: '#6a7985',
          },
        },
        formatter: (params: any) => {
          if (!Array.isArray(params) || params.length === 0) return '';
          const date = params[0].axisValue;
          let result = `<div style="font-weight:500;margin-bottom:4px">${date}</div>`;
          params.forEach((item: any) => {
            const value = item.value?.toLocaleString() || 0;
            const unit = item.seriesName === '花费' ? '¥' : '';
            result += `<div style="display:flex;align-items:center;gap:8px;margin:2px 0">
              <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${item.color}"></span>
              <span>${item.seriesName}: ${unit}${value}</span>
            </div>`;
          });
          return result;
        },
      },
      legend: {
        data: [showSpend ? '花费' : '', showLeads ? '线索' : ''].filter(Boolean),
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
        boundaryGap: false,
        data: dates,
        axisLine: {
          lineStyle: {
            color: '#e8e8e8',
          },
        },
        axisLabel: {
          color: '#666',
          formatter: (value: string) => dayjs(value).format('MM/DD'),
        },
      },
      yAxis: showSpend && showLeads ? [
        {
          type: 'value',
          name: '花费(¥)',
          position: 'left',
          axisLine: {
            show: true,
            lineStyle: {
              color: '#0ea5e9',
            },
          },
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
          axisLine: {
            show: true,
            lineStyle: {
              color: '#10b981',
            },
          },
          axisLabel: {
            color: '#666',
          },
          splitLine: {
            show: false,
          },
        },
      ] : [
        {
          type: 'value',
          name: showSpend ? '花费(¥)' : '线索',
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
      ],
      series,
    };
  }, [data, showSpend, showLeads, title]);

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

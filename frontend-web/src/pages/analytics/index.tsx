/**
 * 交叉分析页面
 * 广告计划与课程交叉分析
 */
import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  DatePicker,
  Select,
  Tag,
  message,
  Spin,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';
import { analyticsApi } from '@/api';
import type { CrossTableRow } from '@/types';

const { RangePicker } = DatePicker;

export const AnalyticsPage: React.FC = () => {
  const [data, setData] = useState<CrossTableRow[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().subtract(30, 'day'),
    dayjs(),
  ]);

  // 加载数据
  const fetchData = async () => {
    setIsLoading(true);
    try {
      const response = await analyticsApi.getCrossTable({
        page: 1,
        page_size: 100,
      });
      setData(response.data.items);
      setTotal(response.data.total);
    } catch (error) {
      message.error('获取数据失败');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // 导出数据
  const handleExport = async () => {
    try {
      const response = await analyticsApi.exportCrossTable({
        start_date: dateRange[0].format('YYYY-MM-DD'),
        end_date: dateRange[1].format('YYYY-MM-DD'),
      });
      
      // 创建下载
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `交叉分析_${dayjs().format('YYYY-MM-DD')}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      message.success('导出成功');
    } catch (error) {
      message.error('导出失败');
    }
  };

  // 表格列定义
  const columns: ColumnsType<CrossTableRow> = [
    {
      title: '广告计划',
      dataIndex: 'campaign_name',
      key: 'campaign_name',
      width: 200,
    },
    {
      title: '课程/产品',
      dataIndex: 'course_name',
      key: 'course_name',
      width: 150,
      render: (name: string) => name || '-',
    },
    {
      title: '花费',
      dataIndex: 'spend',
      key: 'spend',
      width: 120,
      sorter: (a, b) => a.spend - b.spend,
      render: (spend: number) => `¥${spend.toLocaleString()}`,
    },
    {
      title: '线索',
      dataIndex: 'leads',
      key: 'leads',
      width: 100,
      sorter: (a, b) => a.leads - b.leads,
      render: (leads: number) => leads.toLocaleString(),
    },
    {
      title: '成交',
      dataIndex: 'deals',
      key: 'deals',
      width: 100,
      sorter: (a, b) => a.deals - b.deals,
      render: (deals: number) => deals.toLocaleString(),
    },
    {
      title: 'CPL',
      key: 'cpl',
      width: 100,
      render: (_, record) => {
        const cpl = record.spend / Math.max(record.leads, 1);
        return `¥${cpl.toFixed(2)}`;
      },
    },
    {
      title: 'ROI',
      dataIndex: 'roi',
      key: 'roi',
      width: 100,
      sorter: (a, b) => a.roi - b.roi,
      render: (roi: number) => (
        <Tag color={roi >= 1 ? 'green' : 'orange'}>
          {roi.toFixed(2)}:1
        </Tag>
      ),
    },
  ];

  // 图表配置
  const chartOption: EChartsOption = {
    title: {
      text: '广告计划效果分布',
      left: 0,
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    legend: {
      data: ['花费', '线索'],
      right: 0,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '60px',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: data.slice(0, 10).map(d => d.campaign_name),
      axisLabel: {
        rotate: 30,
        interval: 0,
      },
    },
    yAxis: [
      {
        type: 'value',
        name: '花费(¥)',
        axisLabel: {
          formatter: (value: number) => `${(value / 1000).toFixed(0)}k`,
        },
      },
      {
        type: 'value',
        name: '线索',
        position: 'right',
      },
    ],
    series: [
      {
        name: '花费',
        type: 'bar',
        data: data.slice(0, 10).map(d => d.spend),
        itemStyle: { color: '#0ea5e9' },
      },
      {
        name: '线索',
        type: 'bar',
        yAxisIndex: 1,
        data: data.slice(0, 10).map(d => d.leads),
        itemStyle: { color: '#10b981' },
      },
    ],
  };

  return (
    <div className="page-container">
      {/* 页面头部 */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">交叉分析</h1>
          <p className="text-gray-500">广告计划与课程的转化效果分析</p>
        </div>
        <Space>
          <RangePicker
            value={dateRange}
            onChange={(dates) => dates && setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs])}
          />
          <Button
            icon={<DownloadOutlined />}
            onClick={handleExport}
          >
            导出 CSV
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchData}
          >
            刷新
          </Button>
        </Space>
      </div>

      {/* 图表 */}
      <Card className="mb-4">
        {isLoading ? (
          <div className="flex items-center justify-center h-80">
            <Spin />
          </div>
        ) : (
          <ReactECharts
            option={chartOption}
            style={{ height: 320 }}
            opts={{ renderer: 'canvas' }}
          />
        )}
      </Card>

      {/* 数据表格 */}
      <Card title="详细数据">
        <Table
          columns={columns}
          dataSource={data}
          rowKey="campaign_id"
          loading={isLoading}
          pagination={{
            total,
            pageSize: 20,
            showTotal: (t) => `共 ${t} 条`,
          }}
          scroll={{ x: 1000 }}
        />
      </Card>
    </div>
  );
};

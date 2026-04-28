/**
 * 报表页面
 * 报表生成和下载
 */
import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  DatePicker,
  Form,
  Select,
  message,
  Empty,
  Spin,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  PlusOutlined,
  DownloadOutlined,
  FileTextOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { reportsApi } from '@/api';
import { InsightCard } from '@/components';
import type { Report, InsightCard as InsightCardType } from '@/types';

const { RangePicker } = DatePicker;

const REPORT_TYPE_OPTIONS = [
  { label: 'ROI 日报', value: 'daily_roi' },
  { label: 'ROI 周报', value: 'weekly_roi' },
  { label: 'ROI 月报', value: 'monthly_roi' },
  { label: '渠道分析', value: 'channel_analysis' },
];

export const ReportsPage: React.FC = () => {
  const [reports, setReports] = useState<Report[]>([]);
  const [insights, setInsights] = useState<InsightCardType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [generateModalVisible, setGenerateModalVisible] = useState(false);
  const [insightModalVisible, setInsightModalVisible] = useState(false);
  const [currentReportId, setCurrentReportId] = useState<string | null>(null);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [form] = Form.useForm();

  // 加载报表列表
  const fetchReports = async () => {
    setIsLoading(true);
    try {
      const response = await reportsApi.list();
      setReports(response.data);
    } catch (error) {
      message.error('获取报表列表失败');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  // 生成报表
  const handleGenerate = async (values: { report_type: string; date_range: [dayjs.Dayjs, dayjs.Dayjs] }) => {
    try {
      await reportsApi.generate({
        report_type: values.report_type,
        start_date: values.date_range[0].format('YYYY-MM-DD'),
        end_date: values.date_range[1].format('YYYY-MM-DD'),
      });
      message.success('报表生成任务已提交');
      setGenerateModalVisible(false);
      form.resetFields();
      fetchReports();
    } catch (error) {
      message.error('生成失败');
    }
  };

  // 下载报表
  const handleDownload = async (report: Report) => {
    try {
      const response = await reportsApi.download(report.id);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      const ext = report.report_type.includes('excel') ? 'xlsx' : 'pdf';
      link.setAttribute('download', `报表_${report.report_type}_${dayjs().format('YYYY-MM-DD')}.${ext}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      message.success('下载成功');
    } catch (error) {
      message.error('下载失败');
    }
  };

  // 查看行动建议
  const handleViewInsights = async (report: Report) => {
    setSelectedReport(report);
    setIsLoading(true);
    setInsightModalVisible(true);
    try {
      const response = await reportsApi.getInsights(report.id);
      setInsights(response.data);
    } catch (error) {
      message.error('获取行动建议失败');
    } finally {
      setIsLoading(false);
    }
  };

  // 表格列定义
  const columns: ColumnsType<Report> = [
    {
      title: '报表类型',
      dataIndex: 'report_type',
      key: 'report_type',
      width: 150,
      render: (type: string) => {
        const option = REPORT_TYPE_OPTIONS.find(o => o.value === type);
        return option?.label || type;
      },
    },
    {
      title: '时间范围',
      key: 'date_range',
      width: 200,
      render: (_, record) => (
        <span>
          {dayjs(record.date_range.start).format('YYYY-MM-DD')} 至{' '}
          {dayjs(record.date_range.end).format('YYYY-MM-DD')}
        </span>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const config: Record<string, { text: string; color: string }> = {
          generating: { text: '生成中', color: 'processing' },
          ready: { text: '就绪', color: 'success' },
          failed: { text: '失败', color: 'error' },
        };
        return <Tag color={config[status]?.color}>{config[status]?.text || status}</Tag>;
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_, record) => (
        <Space>
          {record.status === 'ready' && (
            <>
              <Button
                type="link"
                size="small"
                icon={<DownloadOutlined />}
                onClick={() => handleDownload(record)}
              >
                下载
              </Button>
              <Button
                type="link"
                size="small"
                icon={<FileTextOutlined />}
                onClick={() => handleViewInsights(record)}
              >
                行动建议
              </Button>
            </>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div className="page-container">
      {/* 页面头部 */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">报表中心</h1>
          <p className="text-gray-500">生成和下载 ROI 分析报表</p>
        </div>
        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setGenerateModalVisible(true)}
          >
            生成报表
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchReports}
          >
            刷新
          </Button>
        </Space>
      </div>

      {/* 报表列表 */}
      <Card>
        {reports.length === 0 && !isLoading ? (
          <Empty description="暂无报表">
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setGenerateModalVisible(true)}
            >
              生成第一份报表
            </Button>
          </Empty>
        ) : (
          <Table
            columns={columns}
            dataSource={reports}
            rowKey="id"
            loading={isLoading}
            pagination={{
              pageSize: 10,
              showTotal: (t) => `共 ${t} 份报表`,
            }}
          />
        )}
      </Card>

      {/* 生成报表弹窗 */}
      <Modal
        title="生成报表"
        open={generateModalVisible}
        onCancel={() => setGenerateModalVisible(false)}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleGenerate}
          initialValues={{
            report_type: 'daily_roi',
            date_range: [dayjs().subtract(7, 'day'), dayjs()],
          }}
        >
          <Form.Item
            name="report_type"
            label="报表类型"
            rules={[{ required: true }]}
          >
            <Select options={REPORT_TYPE_OPTIONS} />
          </Form.Item>
          <Form.Item
            name="date_range"
            label="时间范围"
            rules={[{ required: true }]}
          >
            <RangePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item className="mb-0">
            <Space className="w-full justify-end">
              <Button onClick={() => setGenerateModalVisible(false)}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                生成
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 行动建议弹窗 */}
      <Modal
        title="行动建议"
        open={insightModalVisible}
        onCancel={() => setInsightModalVisible(false)}
        footer={null}
        width={800}
      >
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <Spin />
          </div>
        ) : insights.length === 0 ? (
          <Empty description="暂无行动建议" />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 py-4">
            {insights.map((insight) => (
              <InsightCard key={insight.id} insight={insight} />
            ))}
          </div>
        )}
      </Modal>
    </div>
  );
};

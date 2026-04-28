/**
 * CRM 线索管理页面
 * Excel 导入和线索列表
 */
import React, { useState, useRef } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Upload,
  Tag,
  Modal,
  message,
  Select,
  DatePicker,
  Form,
  Popconfirm,
} from 'antd';
import {
  PlusOutlined,
  UploadOutlined,
  DeleteOutlined,
  SearchOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { UploadProps, UploadFile } from 'antd/es/upload';
import dayjs from 'dayjs';
import {
  SmartFieldMapper,
  AttributionConfirm,
  ProgressOverlay,
} from '@/components';
import { useImportProgress } from '@/hooks';
import { crmApi } from '@/api';
import type { CRMLead, ImportProgress, ImportBatch } from '@/types';

const { RangePicker } = DatePicker;

export const CRMPage: React.FC = () => {
  // 状态
  const [leads, setLeads] = useState<CRMLead[]>([]);
  const [batches, setBatches] = useState<ImportBatch[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  
  // 上传相关
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [currentBatchId, setCurrentBatchId] = useState<string | null>(null);
  const [uploadFileList, setUploadFileList] = useState<UploadFile[]>([]);
  
  // 归因确认
  const [attributionModalVisible, setAttributionModalVisible] = useState(false);
  
  // 存储字段映射（用于传递给归因确认后的导入）
  const [confirmedMappings, setConfirmedMappings] = useState<Record<string, string> | null>(null);
  
  // 导入进度
  const { progress, isLoading: isProgressLoading, error: progressError, startPolling } = useImportProgress();

  // 筛选条件
  const [filters, setFilters] = useState({
    deal_status: undefined as string | undefined,
    date_range: undefined as [dayjs.Dayjs, dayjs.Dayjs] | undefined,
  });

  // 加载线索数据
  const fetchLeads = async () => {
    setIsLoading(true);
    try {
      const response = await crmApi.getLeads({
        page: 1,
        page_size: 100,
        deal_status: filters.deal_status,
      });
      setLeads(response.data.items);
      setTotal(response.data.total);
    } catch (error) {
      message.error('获取线索列表失败');
    } finally {
      setIsLoading(false);
    }
  };

  // 加载导入批次
  const fetchBatches = async () => {
    try {
      const response = await crmApi.getBatches();
      setBatches(response.data.items);
    } catch (error) {
      console.error('获取导入批次失败', error);
    }
  };

  React.useEffect(() => {
    fetchLeads();
    fetchBatches();
  }, [filters]);

  // 处理文件上传
  const handleUpload: UploadProps['customRequest'] = async (options) => {
    const { file, onSuccess, onError } = options;
    const formData = new FormData();
    formData.append('file', file as File);

    try {
      const response = await crmApi.upload(formData, (percent) => {
        // 上传进度
      });
      
      setCurrentBatchId(response.data.batch_id);
      startPolling(response.data.task_id);
      
      message.success('文件上传成功，正在解析...');
      setUploadModalVisible(false);
      // 先显示字段映射弹窗（不直接打开归因弹窗）
      setUploadFileList([]);
    } catch (error) {
      message.error('文件上传失败');
      onError?.(error as Error);
    }
  };

  // 处理字段映射确认
  const handleMappingConfirm = (mappings: Record<string, string>) => {
    // 存储字段映射，确认归因后使用
    setConfirmedMappings(mappings);
    // 确认字段映射后，显示归因确认弹窗
    setAttributionModalVisible(true);
  };

  // 处理归因确认并开始导入
  const handleAttributionConfirm = (rules: Record<string, string>) => {
    if (currentBatchId && confirmedMappings) {
      // 合并字段映射和归因规则
      const combinedMappings = {
        ...confirmedMappings,
        ...rules,
      };
      crmApi.confirmMapping(currentBatchId, combinedMappings).then(() => {
        message.success('导入任务已提交');
        fetchBatches();
        // 清理状态
        setAttributionModalVisible(false);
        setCurrentBatchId(null);
        setConfirmedMappings(null);
        setUploadFileList([]);
      }).catch(() => {
        message.error('导入失败');
      });
    }
  };

  // 删除线索
  const handleDeleteLeads = async () => {
    // TODO: 实现批量删除
    message.info('批量删除功能开发中');
  };

  // 更新线索状态
  const handleUpdateLeadStatus = async (leadId: string, status: string) => {
    try {
      await crmApi.updateLead(leadId, { deal_status: status as any });
      message.success('状态已更新');
      fetchLeads();
    } catch (error) {
      message.error('更新失败');
    }
  };

  // 表格列定义
  const columns: ColumnsType<CRMLead> = [
    {
      title: '姓名',
      dataIndex: 'name',
      key: 'name',
      width: 120,
    },
    {
      title: '来源渠道',
      dataIndex: 'source_channel',
      key: 'source_channel',
      width: 150,
    },
    {
      title: '课程/产品',
      dataIndex: 'course_name',
      key: 'course_name',
      width: 150,
    },
    {
      title: '成交状态',
      dataIndex: 'deal_status',
      key: 'deal_status',
      width: 100,
      render: (status: string) => {
        const colors: Record<string, string> = {
          deal: 'green',
          following: 'blue',
          no_deal: 'default',
        };
        const texts: Record<string, string> = {
          deal: '已成交',
          following: '跟进中',
          no_deal: '未成交',
        };
        return <Tag color={colors[status]}>{texts[status] || status}</Tag>;
      },
    },
    {
      title: '成交金额',
      dataIndex: 'deal_amount',
      key: 'deal_amount',
      width: 120,
      render: (amount: number) => amount ? `¥${amount.toLocaleString()}` : '-',
    },
    {
      title: '导入时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
  ];

  return (
    <div className="page-container">
      {/* 页面头部 */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">CRM 线索</h1>
          <p className="text-gray-500">管理您的客户线索和导入历史</p>
        </div>
        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setUploadModalVisible(true)}
          >
            导入线索
          </Button>
        </Space>
      </div>

      {/* 筛选区域 */}
      <Card className="mb-4" styles={{ body: { padding: '16px 24px' } }}>
        <Form layout="inline">
          <Form.Item label="成交状态">
            <Select
              placeholder="全部状态"
              allowClear
              style={{ width: 120 }}
              value={filters.deal_status}
              onChange={(value) => setFilters({ ...filters, deal_status: value })}
            >
              <Select.Option value="deal">已成交</Select.Option>
              <Select.Option value="following">跟进中</Select.Option>
              <Select.Option value="no_deal">未成交</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item label="时间范围">
            <RangePicker
              value={filters.date_range}
              onChange={(dates) => setFilters({ ...filters, date_range: dates as any })}
            />
          </Form.Item>
          <Form.Item>
            <Button icon={<SearchOutlined />}>搜索</Button>
          </Form.Item>
        </Form>
      </Card>

      {/* 导入批次记录 */}
      {batches.length > 0 && (
        <Card className="mb-4" title="最近导入">
          <Space wrap>
            {batches.slice(0, 5).map((batch) => (
              <Tag key={batch.id} color={batch.status === 'completed' ? 'green' : 'blue'}>
                {batch.filename} ({batch.success_rows}/{batch.total_rows})
              </Tag>
            ))}
          </Space>
        </Card>
      )}

      {/* 线索表格 */}
      <Card>
        <div className="flex justify-between items-center mb-4">
          <span className="text-gray-500">
            共 {total} 条线索
          </span>
          <Space>
            {selectedRowKeys.length > 0 && (
              <Popconfirm
                title="确定要删除选中的线索吗？"
                onConfirm={handleDeleteLeads}
              >
                <Button danger icon={<DeleteOutlined />}>
                  批量删除 ({selectedRowKeys.length})
                </Button>
              </Popconfirm>
            )}
            <Button icon={<ReloadOutlined />} onClick={fetchLeads}>
              刷新
            </Button>
          </Space>
        </div>
        <Table
          columns={columns}
          dataSource={leads}
          rowKey="id"
          loading={isLoading}
          rowSelection={{
            selectedRowKeys,
            onChange: setSelectedRowKeys,
          }}
          pagination={{
            total,
            pageSize: 100,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </Card>

      {/* 上传弹窗 */}
      <Modal
        title="导入线索"
        open={uploadModalVisible}
        onCancel={() => setUploadModalVisible(false)}
        footer={null}
      >
        <Upload.Dragger
          accept=".xlsx,.xls,.csv"
          fileList={uploadFileList}
          onChange={({ fileList }) => setUploadFileList(fileList)}
          customRequest={handleUpload}
          maxCount={1}
        >
          <p className="text-4xl mb-4">
            <UploadOutlined />
          </p>
          <p className="text-base">点击或拖拽上传 Excel/CSV 文件</p>
          <p className="text-gray-400 text-sm mt-2">
            支持 .xlsx, .xls, .csv 格式，单文件不超过 10MB
          </p>
        </Upload.Dragger>
      </Modal>

      {/* 字段映射弹窗 */}
      <Modal
        title="确认字段映射"
        open={!!currentBatchId && !attributionModalVisible}
        onCancel={() => {
          setCurrentBatchId(null);
          setUploadFileList([]);
        }}
        footer={null}
        width={700}
      >
        {currentBatchId && (
          <SmartFieldMapper
            batchId={currentBatchId}
            onConfirm={handleMappingConfirm}
            onCancel={() => {
              setCurrentBatchId(null);
              setUploadFileList([]);
            }}
          />
        )}
      </Modal>

      {/* 归因确认弹窗 */}
      <AttributionConfirm
        open={attributionModalVisible}
        batchId={currentBatchId || ''}
        onConfirm={handleAttributionConfirm}
        onCancel={() => {
          setAttributionModalVisible(false);
          setCurrentBatchId(null);
          setConfirmedMappings(null);
        }}
      />

      {/* 导入进度浮窗 */}
      <ProgressOverlay
        progress={progress}
        isLoading={isProgressLoading}
        error={progressError}
        onClose={() => {}}
        filename={uploadFileList[0]?.name}
      />
    </div>
  );
};

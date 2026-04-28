/**
 * 智能字段映射组件
 * Excel 导入时的字段匹配确认
 */
import React, { useState, useEffect } from 'react';
import { Table, Select, Tag, Space, Button, Spin, Alert, Tooltip } from 'antd';
import { CheckCircleOutlined, WarningOutlined, QuestionCircleOutlined } from '@ant-design/icons';
import { crmApi } from '@/api';
import { getFieldLabel } from '@/utils';
import type { FieldMappingResponse, FieldMapping } from '@/types';

interface SmartFieldMapperProps {
  batchId: string;
  onConfirm: (mappings: Record<string, string>) => void;
  onCancel: () => void;
  loading?: boolean;
}

export const SmartFieldMapper: React.FC<SmartFieldMapperProps> = ({
  batchId,
  onConfirm,
  onCancel,
  loading = false,
}) => {
  const [data, setData] = useState<FieldMappingResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mappings, setMappings] = useState<Record<string, string>>({});

  useEffect(() => {
    fetchMappings();
  }, [batchId]);

  const fetchMappings = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await crmApi.previewMapping(batchId);
      setData(response.data);
      
      // 初始化映射
      const initialMappings: Record<string, string> = {};
      response.data.field_mappings.forEach((fm) => {
        if (fm.field && fm.matchedColumn) {
          initialMappings[fm.field] = fm.matchedColumn;
        }
      });
      setMappings(initialMappings);
    } catch (err) {
      setError('获取字段映射失败');
    } finally {
      setIsLoading(false);
    }
  };

  const handleMappingChange = (field: string, column: string) => {
    setMappings(prev => ({
      ...prev,
      [field]: column,
    }));
  };

  const handleConfirm = () => {
    // 验证必填字段
    const requiredFields = ['name', 'phone'];
    const missingFields = requiredFields.filter(f => !mappings[f]);
    
    if (missingFields.length > 0) {
      return;
    }
    
    onConfirm(mappings);
  };

  // 获取置信度标签颜色
  const getConfidenceColor = (confidence: FieldMapping['confidence']) => {
    switch (confidence) {
      case 'auto':
        return 'green';
      case 'suggested':
        return 'orange';
      default:
        return 'default';
    }
  };

  const getConfidenceText = (confidence: FieldMapping['confidence']) => {
    switch (confidence) {
      case 'auto':
        return '自动匹配';
      case 'suggested':
        return '建议匹配';
      default:
        return '未匹配';
    }
  };

  // 统计映射情况
  const matchedCount = data?.field_mappings.filter(fm => fm.field && fm.confidence !== 'none').length || 0;
  const suggestedCount = data?.field_mappings.filter(fm => fm.confidence === 'suggested').length || 0;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Spin tip="正在分析字段映射..." />
      </div>
    );
  }

  if (error || !data) {
    return (
      <Alert
        type="error"
        message={error || '加载失败'}
        action={
          <Button size="small" onClick={fetchMappings}>
            重试
          </Button>
        }
      />
    );
  }

  const columns = [
    {
      title: '标准字段',
      dataIndex: 'field',
      key: 'field',
      width: 180,
      render: (field: string, record: FieldMapping) => (
        <Space>
          <span className="font-medium">{field ? getFieldLabel(field) : '-'}</span>
          {field && (
            <Tag
              color={getConfidenceColor(record.confidence)}
              icon={record.confidence === 'none' ? <WarningOutlined /> : undefined}
            >
              {getConfidenceText(record.confidence)}
            </Tag>
          )}
        </Space>
      ),
    },
    {
      title: 'Excel 列名',
      dataIndex: 'matchedColumn',
      key: 'matchedColumn',
      width: 200,
      render: (column: string | undefined, record: FieldMapping) => (
        <Select
          placeholder="选择对应的列"
          value={column}
          onChange={(value) => handleMappingChange(record.field, value)}
          className="w-full"
          allowClear
        >
          {data.columns.map((col) => (
            <Select.Option key={col} value={col}>
              {col}
            </Select.Option>
          ))}
        </Select>
      ),
    },
    {
      title: '说明',
      key: 'description',
      render: (_: any, record: FieldMapping) => (
        <Tooltip title={record.field ? `请将"${record.field}"字段映射到Excel中对应的列` : '此列暂未识别为标准字段'}>
          <QuestionCircleOutlined className="text-gray-400" />
        </Tooltip>
      ),
    },
  ];

  return (
    <div>
      {/* 头部提示 */}
      <Alert
        type="info"
        showIcon
        icon={<CheckCircleOutlined />}
        message="字段智能匹配完成"
        description={
          <span>
            已自动匹配 {matchedCount} 个字段，
            {suggestedCount > 0 && <span className="text-orange-500">其中 {suggestedCount} 个需要确认</span>}
            。请检查并确认映射关系正确。
          </span>
        }
        className="mb-4"
      />

      {/* 必填字段提示 */}
      {!mappings.name || !mappings.phone ? (
        <Alert
          type="warning"
          message="请确保「姓名」和「手机号」字段已正确映射"
          className="mb-4"
          icon={<WarningOutlined />}
        />
      ) : null}

      {/* 字段映射表格 */}
      <Table
        columns={columns}
        dataSource={data.field_mappings}
        rowKey={(_, index) => String(index)}
        pagination={false}
        className="mb-4"
      />

      {/* 底部操作 */}
      <div className="flex justify-end gap-2">
        <Button onClick={onCancel}>
          取消导入
        </Button>
        <Button
          type="primary"
          onClick={handleConfirm}
          loading={loading}
          disabled={!mappings.name || !mappings.phone}
        >
          确认映射，开始导入
        </Button>
      </div>
    </div>
  );
};

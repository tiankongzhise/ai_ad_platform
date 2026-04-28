/**
 * 归因确认弹窗组件
 * 导入时自动分析并确认归因规则
 */
import React, { useState, useEffect } from 'react';
import { Modal, List, Tag, Button, Space, Alert, Spin, Checkbox } from 'antd';
import { CheckCircleOutlined, WarningOutlined, UnorderedListOutlined } from '@ant-design/icons';
import { crmApi } from '@/api';
import type { AttributionSuggestion } from '@/types';

interface AttributionConfirmProps {
  open: boolean;
  batchId: string;
  onConfirm: (rules: Record<string, string>) => void;
  onCancel: () => void;
  loading?: boolean;
}

export const AttributionConfirm: React.FC<AttributionConfirmProps> = ({
  open,
  batchId,
  onConfirm,
  onCancel,
  loading = false,
}) => {
  const [suggestion, setSuggestion] = useState<AttributionSuggestion | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedRules, setSelectedRules] = useState<Record<string, string>>({});
  const [confirmed, setConfirmed] = useState(false);

  useEffect(() => {
    if (open && batchId) {
      fetchSuggestion();
    }
  }, [open, batchId]);

  const fetchSuggestion = async () => {
    setIsLoading(true);
    try {
      const response = await crmApi.getAttributionSuggest(batchId);
      setSuggestion(response.data);
      
      // 初始化选中的规则
      const initialRules: Record<string, string> = {};
      response.data.suggestions.forEach((s) => {
        if (s.matched_platform) {
          initialRules[s.channel] = s.matched_platform;
        }
      });
      setSelectedRules(initialRules);
    } catch (error) {
      console.error('获取归因建议失败', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRuleToggle = (channel: string, platform: string) => {
    setSelectedRules(prev => ({
      ...prev,
      [channel]: prev[channel] === platform ? '' : platform,
    }));
  };

  const handleConfirm = () => {
    if (!confirmed) return;
    onConfirm(selectedRules);
  };

  if (isLoading) {
    return (
      <Modal
        open={open}
        title="归因规则确认"
        footer={null}
        onCancel={onCancel}
        width={600}
      >
        <div className="flex items-center justify-center py-16">
          <Spin tip="正在分析归因规则..." />
        </div>
      </Modal>
    );
  }

  if (!suggestion) {
    return null;
  }

  const hasMatched = suggestion.matched_count > 0;
  const hasUnmatched = suggestion.unmatched_count > 0;

  return (
    <Modal
      open={open}
      title={
        <div className="flex items-center gap-2">
          <UnorderedListOutlined />
          <span>归因规则确认</span>
        </div>
      }
      onCancel={onCancel}
      width={600}
      footer={
        <Space>
          <Button onClick={onCancel}>取消</Button>
          <Button
            type="primary"
            onClick={handleConfirm}
            loading={loading}
            disabled={!confirmed}
          >
            确认并开始导入
          </Button>
        </Space>
      }
    >
      <div className="py-4">
        {/* 统计概览 */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-green-50 rounded-lg p-4">
            <div className="text-2xl font-bold text-green-600">
              {suggestion.matched_count}
            </div>
            <div className="text-sm text-gray-600">已匹配线索</div>
          </div>
          <div className="bg-orange-50 rounded-lg p-4">
            <div className="text-2xl font-bold text-orange-600">
              {suggestion.unmatched_count}
            </div>
            <div className="text-sm text-gray-600">待确认线索</div>
          </div>
        </div>

        {/* 匹配建议 */}
        {hasMatched && (
          <div className="mb-6">
            <h4 className="font-medium mb-3 flex items-center gap-2">
              <CheckCircleOutlined className="text-green-500" />
              自动识别的渠道
            </h4>
            <List
              size="small"
              bordered
              dataSource={suggestion.suggestions.filter(s => s.matched_platform)}
              renderItem={(item) => (
                <List.Item>
                  <div className="flex items-center justify-between w-full">
                    <Space>
                      <span>"{item.channel}"</span>
                      <ArrowRightOutlined className="text-gray-400" />
                    </Space>
                    <Tag color={item.matched_platform === 'juliang' ? 'red' : 'blue'}>
                      {item.matched_platform === 'juliang' ? '巨量引擎' : '百度营销'}
                    </Tag>
                  </div>
                </List.Item>
              )}
            />
          </div>
        )}

        {/* 未匹配项 */}
        {hasUnmatched && (
          <div className="mb-6">
            <h4 className="font-medium mb-3 flex items-center gap-2">
              <WarningOutlined className="text-orange-500" />
              未识别的渠道（需要确认）
            </h4>
            <div className="space-y-2">
              {suggestion.unmatched_sample.slice(0, 5).map((channel, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-2 border rounded"
                >
                  <span className="text-gray-600">"{channel}"</span>
                  <Space>
                    <Checkbox
                      checked={selectedRules[channel] === 'juliang'}
                      onChange={() => handleRuleToggle(channel, 'juliang')}
                    >
                      巨量
                    </Checkbox>
                    <Checkbox
                      checked={selectedRules[channel] === 'baidu'}
                      onChange={() => handleRuleToggle(channel, 'baidu')}
                    >
                      百度
                    </Checkbox>
                    <Checkbox
                      checked={selectedRules[channel] === 'other'}
                      onChange={() => handleRuleToggle(channel, 'other')}
                    >
                      其他
                    </Checkbox>
                  </Space>
                </div>
              ))}
              {suggestion.unmatched_sample.length > 5 && (
                <div className="text-sm text-gray-500 text-center">
                  还有 {suggestion.unmatched_sample.length - 5} 个未显示...
                </div>
              )}
            </div>
          </div>
        )}

        {/* 确认提示 */}
        <Alert
          type="info"
          message="确认后系统将根据您选择的归因规则计算 ROI"
          className="mb-4"
        />

        <Checkbox
          checked={confirmed}
          onChange={(e) => setConfirmed(e.target.checked)}
        >
          我已确认归因规则，理解这些规则将影响 ROI 计算结果
        </Checkbox>
      </div>
    </Modal>
  );
};

// 需要引入 ArrowRightOutlined
import { ArrowRightOutlined } from '@ant-design/icons';

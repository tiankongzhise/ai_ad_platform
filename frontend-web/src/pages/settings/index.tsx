/**
 * 设置页面
 * 归因规则、账户设置等
 */
import React, { useState, useEffect } from 'react';
import {
  Card,
  Tabs,
  Form,
  Input,
  Button,
  Table,
  Space,
  Tag,
  Modal,
  message,
  Popconfirm,
} from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { settingsApi } from '@/api';

interface AttributionRule {
  id: string;
  platform: string;
  keywords: string[];
  created_at: string;
}

export const SettingsPage: React.FC = () => {
  // 归因规则状态
  const [rules, setRules] = useState<AttributionRule[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [ruleModalVisible, setRuleModalVisible] = useState(false);
  const [editingRule, setEditingRule] = useState<AttributionRule | null>(null);
  const [form] = Form.useForm();

  // 加载归因规则
  const fetchRules = async () => {
    setIsLoading(true);
    try {
      const response = await settingsApi.getAttributionRules();
      setRules(response.data);
    } catch (error) {
      message.error('获取归因规则失败');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, []);

  // 创建/编辑规则
  const handleSaveRule = async (values: { platform: string; keywords: string }) => {
    try {
      const keywords = values.keywords.split(',').map(k => k.trim()).filter(Boolean);
      
      if (editingRule) {
        await settingsApi.updateAttributionRule(editingRule.id, { keywords });
        message.success('规则已更新');
      } else {
        await settingsApi.createAttributionRule({ platform: values.platform, keywords });
        message.success('规则已创建');
      }
      
      setRuleModalVisible(false);
      form.resetFields();
      setEditingRule(null);
      fetchRules();
    } catch (error) {
      message.error('保存失败');
    }
  };

  // 删除规则
  const handleDeleteRule = async (ruleId: string) => {
    try {
      await settingsApi.deleteAttributionRule(ruleId);
      message.success('规则已删除');
      fetchRules();
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 编辑规则
  const handleEditRule = (rule: AttributionRule) => {
    setEditingRule(rule);
    form.setFieldsValue({
      platform: rule.platform,
      keywords: rule.keywords.join(', '),
    });
    setRuleModalVisible(true);
  };

  // 规则表格列
  const ruleColumns: ColumnsType<AttributionRule> = [
    {
      title: '平台',
      dataIndex: 'platform',
      key: 'platform',
      width: 150,
      render: (platform: string) => (
        <Tag color={platform === 'juliang' ? 'red' : 'blue'}>
          {platform === 'juliang' ? '巨量引擎' : platform === 'baidu' ? '百度营销' : '其他'}
        </Tag>
      ),
    },
    {
      title: '关键词',
      dataIndex: 'keywords',
      key: 'keywords',
      render: (keywords: string[]) => (
        <Space wrap>
          {keywords.map((k, i) => (
            <Tag key={i}>{k}</Tag>
          ))}
        </Space>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEditRule(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除此规则吗？"
            onConfirm={() => handleDeleteRule(record.id)}
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className="page-container">
      {/* 页面头部 */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold">设置</h1>
        <p className="text-gray-500">管理归因规则和账户设置</p>
      </div>

      <Tabs
        items={[
          {
            key: 'attribution',
            label: '归因规则',
            children: (
              <Card
                title="归因规则"
                extra={
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => {
                      setEditingRule(null);
                      form.resetFields();
                      setRuleModalVisible(true);
                    }}
                  >
                    添加规则
                  </Button>
                }
              >
                <p className="text-gray-500 mb-4">
                  设置渠道关键词映射，用于自动识别线索来源并计算 ROI。
                  例如：巨量引擎渠道包含"抖音"、"头条"等关键词。
                </p>
                <Table
                  columns={ruleColumns}
                  dataSource={rules}
                  rowKey="id"
                  loading={isLoading}
                  pagination={false}
                />
              </Card>
            ),
          },
          {
            key: 'account',
            label: '账户设置',
            children: (
              <Card title="账户信息">
                <Form layout="vertical">
                  <Form.Item label="机构名称">
                    <Input placeholder="请输入机构名称" />
                  </Form.Item>
                  <Form.Item label="行业细分">
                    <Input placeholder="例如：K12教育培训" />
                  </Form.Item>
                  <Form.Item label="主营课程">
                    <Input placeholder="例如：中小学数学辅导" />
                  </Form.Item>
                  <Form.Item>
                    <Button type="primary">保存</Button>
                  </Form.Item>
                </Form>
              </Card>
            ),
          },
        ]}
      />

      {/* 添加/编辑规则弹窗 */}
      <Modal
        title={editingRule ? '编辑归因规则' : '添加归因规则'}
        open={ruleModalVisible}
        onCancel={() => {
          setRuleModalVisible(false);
          form.resetFields();
          setEditingRule(null);
        }}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveRule}
        >
          <Form.Item
            name="platform"
            label="归属平台"
            rules={[{ required: true, message: '请选择平台' }]}
          >
            <select
              className="ant-input"
              style={{ width: '100%', height: '32px' }}
            >
              <option value="">请选择</option>
              <option value="juliang">巨量引擎（抖音）</option>
              <option value="baidu">百度营销</option>
              <option value="other">其他</option>
            </select>
          </Form.Item>
          <Form.Item
            name="keywords"
            label="渠道关键词"
            rules={[{ required: true, message: '请输入关键词' }]}
            extra="多个关键词用逗号分隔，例如：抖音,头条,douyin,tiktok"
          >
            <Input.TextArea
              rows={3}
              placeholder="请输入关键词，多个用逗号分隔"
            />
          </Form.Item>
          <Form.Item className="mb-0">
            <Space className="w-full justify-end">
              <Button onClick={() => setRuleModalVisible(false)}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                保存
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

/**
 * 广告账户管理页面
 * 巨量引擎/百度营销 OAuth 绑定和管理
 */
import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  message,
  Popconfirm,
  Empty,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  PlusOutlined,
  SyncOutlined,
  DisconnectOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { adAccountApi } from '@/api';
import { formatCurrency } from '@/utils';
import type { AdAccount, AdPlatform } from '@/types';

const PLATFORM_CONFIG: Record<AdPlatform, { name: string; color: string; icon: string }> = {
  juliang: { name: '巨量引擎（抖音）', color: 'red', icon: '🎵' },
  baidu: { name: '百度营销', color: 'blue', icon: '🔍' },
};

const STATUS_CONFIG: Record<string, { text: string; color: string }> = {
  active: { text: '正常', color: 'green' },
  suspended: { text: '已暂停', color: 'default' },
  authorized: { text: '待激活', color: 'orange' },
  expired: { text: '已过期', color: 'red' },
  error: { text: '异常', color: 'red' },
};

export const AdAccountsPage: React.FC = () => {
  const [accounts, setAccounts] = useState<AdAccount[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [syncLoading, setSyncLoading] = useState<string | null>(null);

  // 加载账户列表
  const fetchAccounts = async () => {
    setIsLoading(true);
    try {
      const response = await adAccountApi.list();
      setAccounts(response.data.items);
    } catch (error) {
      message.error('获取广告账户失败');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAccounts();
  }, []);

  // 绑定广告账户
  const handleBindAccount = async (platform: AdPlatform) => {
    try {
      let response;
      if (platform === 'juliang') {
        response = await adAccountApi.getJuliangOAuthUrl();
      } else {
        response = await adAccountApi.getBaiduOAuthUrl();
      }
      
      const { oauth_url } = response.data;
      // 打开授权页面
      window.open(oauth_url, '_blank', 'width=600,height=700');
      
      message.success('已在新窗口打开授权页面');
    } catch (error) {
      message.error('获取授权链接失败，请稍后重试');
    }
  };

  // 断开账户
  const handleDisconnect = async (accountId: string) => {
    try {
      await adAccountApi.delete(accountId);
      message.success('已断开广告账户');
      fetchAccounts();
    } catch (error) {
      message.error('操作失败');
    }
  };

  // 手动同步
  const handleSync = async (accountId: string) => {
    setSyncLoading(accountId);
    try {
      const response = await adAccountApi.manualSync(accountId, { days: 7 });
      message.success(response.data.message);
    } catch (error) {
      message.error('同步失败');
    } finally {
      setSyncLoading(null);
    }
  };

  // 表格列定义
  const columns: ColumnsType<AdAccount> = [
    {
      title: '广告平台',
      dataIndex: 'platform',
      key: 'platform',
      width: 180,
      render: (platform: AdPlatform) => (
        <Space>
          <span>{PLATFORM_CONFIG[platform].icon}</span>
          <Tag color={PLATFORM_CONFIG[platform].color}>
            {PLATFORM_CONFIG[platform].name}
          </Tag>
        </Space>
      ),
    },
    {
      title: '账户名称',
      dataIndex: 'account_name',
      key: 'account_name',
    },
    {
      title: '账户 ID',
      dataIndex: 'account_id',
      key: 'account_id',
      render: (id: string) => (
        <span className="text-gray-500 font-mono text-sm">{id}</span>
      ),
    },
    {
      title: '余额',
      dataIndex: 'balance',
      key: 'balance',
      width: 120,
      render: (balance: number) => formatCurrency(balance),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={STATUS_CONFIG[status]?.color || 'default'}>
          {STATUS_CONFIG[status]?.text || status}
        </Tag>
      ),
    },
    {
      title: '授权时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<SyncOutlined spin={syncLoading === record.id} />}
            onClick={() => handleSync(record.id)}
            disabled={syncLoading === record.id || record.status !== 'active'}
          >
            同步
          </Button>
          <Popconfirm
            title="确定要断开此广告账户吗？"
            description="断开后将在次日停止同步数据"
            onConfirm={() => handleDisconnect(record.id)}
          >
            <Button type="link" size="small" danger>
              断开
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className="page-container">
      {/* 页面头部 */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">广告账户</h1>
          <p className="text-gray-500">管理您的广告平台授权账户</p>
        </div>
        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => handleBindAccount('juliang')}
          >
            绑定巨量引擎
          </Button>
          <Button
            icon={<PlusOutlined />}
            onClick={() => handleBindAccount('baidu')}
          >
            绑定百度营销
          </Button>
        </Space>
      </div>

      {/* 账户列表 */}
      <Card>
        {accounts.length === 0 && !isLoading ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="暂无广告账户"
          >
            <Space direction="vertical">
              <p className="text-gray-400">
                绑定广告平台账户，开始追踪广告效果
              </p>
              <Space>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => handleBindAccount('juliang')}
                >
                  绑定巨量引擎
                </Button>
                <Button
                  icon={<PlusOutlined />}
                  onClick={() => handleBindAccount('baidu')}
                >
                  绑定百度营销
                </Button>
              </Space>
            </Space>
          </Empty>
        ) : (
          <Table
            columns={columns}
            dataSource={accounts}
            rowKey="id"
            loading={isLoading}
            pagination={false}
          />
        )}
      </Card>

      {/* 帮助提示 */}
      <Card className="mt-4" styles={{ body: { padding: '16px 24px' } }}>
        <div className="flex items-start gap-3">
          <CheckCircleOutlined className="text-blue-500 text-lg mt-0.5" />
          <div>
            <h4 className="font-medium mb-1">绑定说明</h4>
            <ul className="text-gray-500 text-sm space-y-1">
              <li>• 巨量引擎：支持抖音、头条、西瓜视频等巨量引擎广告账户</li>
              <li>• 百度营销：支持百度搜索、信息流广告账户</li>
              <li>• 绑定后会自动同步最近 7 天的广告数据</li>
              <li>• 每日凌晨 2 点自动同步前一天的广告数据</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
};

/**
 * 布局组件
 * 包含侧边栏、头部和内容区域
 */
import React, { useState, useEffect } from 'react';
import { Layout as AntLayout, Menu, Avatar, Dropdown, Space, Badge } from 'antd';
import type { MenuProps } from 'antd';
import {
  DashboardOutlined,
  DatabaseOutlined,
  ShopOutlined,
  LineChartOutlined,
  FileTextOutlined,
  SettingOutlined,
  BellOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/store';
import { DemoDataToggle } from '@/components/DemoDataToggle';

const { Header, Sider, Content } = AntLayout;

const MENU_ITEMS: MenuProps['items'] = [
  {
    key: '/dashboard',
    icon: <DashboardOutlined />,
    label: '仪表盘',
  },
  {
    key: '/crm',
    icon: <DatabaseOutlined />,
    label: 'CRM 线索',
  },
  {
    key: '/ad-accounts',
    icon: <ShopOutlined />,
    label: '广告账户',
  },
  {
    key: '/analytics',
    icon: <LineChartOutlined />,
    label: '交叉分析',
  },
  {
    key: '/reports',
    icon: <FileTextOutlined />,
    label: '报表',
  },
  {
    key: '/settings',
    icon: <SettingOutlined />,
    label: '设置',
  },
];

export const Layout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();
  const [collapsed, setCollapsed] = useState(false);

  // 处理菜单点击
  const handleMenuClick: MenuProps['onClick'] = ({ key }) => {
    navigate(key);
  };

  // 处理登出
  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  // 用户菜单
  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人设置',
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ];

  return (
    <AntLayout className="min-h-screen">
      {/* 侧边栏 */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={220}
        className="bg-white"
        style={{
          boxShadow: '2px 0 8px rgba(0,0,0,0.05)',
        }}
      >
        {/* Logo */}
        <div
          className="h-16 flex items-center justify-center border-b"
          style={{ borderColor: '#f0f0f0' }}
        >
          {collapsed ? (
            <span className="text-xl font-bold text-blue-500">Edu</span>
          ) : (
            <span className="text-xl font-bold text-blue-500">EduAdCRM</span>
          )}
        </div>

        {/* 菜单 */}
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={MENU_ITEMS}
          onClick={handleMenuClick}
          className="border-r-0"
        />
      </Sider>

      <AntLayout>
        {/* 头部 */}
        <Header
          className="bg-white flex items-center justify-between px-4"
          style={{
            padding: '0 24px',
            boxShadow: '0 1px 4px rgba(0,0,0,0.05)',
          }}
        >
          <div className="flex items-center gap-4">
            <span
              onClick={() => setCollapsed(!collapsed)}
              className="text-lg cursor-pointer p-2 hover:bg-gray-100 rounded"
            >
              {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            </span>
          </div>

          <div className="flex items-center gap-4">
            {/* 演示数据切换 */}
            <DemoDataToggle />

            {/* 通知 */}
            <Badge count={0} size="small">
              <BellOutlined className="text-lg text-gray-500 cursor-pointer" />
            </Badge>

            {/* 用户信息 */}
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Space className="cursor-pointer">
                <Avatar
                  style={{ backgroundColor: '#0ea5e9' }}
                  icon={<UserOutlined />}
                />
                <span className="text-sm">{user?.email || '用户'}</span>
              </Space>
            </Dropdown>
          </div>
        </Header>

        {/* 内容区域 */}
        <Content
          className="p-6 bg-gray-50"
          style={{
            margin: 0,
            minHeight: 'calc(100vh - 64px)',
          }}
        >
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  );
};

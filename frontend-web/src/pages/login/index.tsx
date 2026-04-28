/**
 * 登录/注册页面
 */
import React, { useState } from 'react';
import { Form, Input, Button, Card, Tabs, message, Alert } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, register, isLoading } = useAuthStore();
  const [activeTab, setActiveTab] = useState('login');
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (values: { email: string; password: string }) => {
    setError(null);
    try {
      await login(values.email, values.password);
      message.success('登录成功');
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || '登录失败，请检查邮箱和密码');
    }
  };

  const handleRegister = async (values: { email: string; password: string; tenant_name: string }) => {
    setError(null);
    try {
      await register(values.email, values.password, values.tenant_name);
      message.success('注册成功，正在跳转...');
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || '注册失败，请稍后重试');
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center"
      style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <Card className="w-full max-w-md shadow-xl">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-blue-500 mb-2">EduAdCRM</h1>
          <p className="text-gray-500">教育广告 ROI 管理平台</p>
        </div>

        {error && (
          <Alert
            type="error"
            message={error}
            className="mb-4"
            closable
            onClose={() => setError(null)}
          />
        )}

        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          centered
          items={[
            {
              key: 'login',
              label: '登录',
              children: (
                <Form
                  name="login"
                  onFinish={handleLogin}
                  layout="vertical"
                  requiredMark={false}
                >
                  <Form.Item
                    name="email"
                    rules={[
                      { required: true, message: '请输入邮箱' },
                      { type: 'email', message: '请输入有效的邮箱地址' },
                    ]}
                  >
                    <Input
                      prefix={<MailOutlined className="text-gray-400" />}
                      placeholder="邮箱"
                      size="large"
                    />
                  </Form.Item>
                  <Form.Item
                    name="password"
                    rules={[{ required: true, message: '请输入密码' }]}
                  >
                    <Input.Password
                      prefix={<LockOutlined className="text-gray-400" />}
                      placeholder="密码"
                      size="large"
                    />
                  </Form.Item>
                  <Form.Item>
                    <Button
                      type="primary"
                      htmlType="submit"
                      size="large"
                      block
                      loading={isLoading}
                    >
                      登录
                    </Button>
                  </Form.Item>
                </Form>
              ),
            },
            {
              key: 'register',
              label: '注册',
              children: (
                <Form
                  name="register"
                  onFinish={handleRegister}
                  layout="vertical"
                  requiredMark={false}
                >
                  <Form.Item
                    name="tenant_name"
                    rules={[{ required: true, message: '请输入机构名称' }]}
                  >
                    <Input
                      prefix={<UserOutlined className="text-gray-400" />}
                      placeholder="机构名称"
                      size="large"
                    />
                  </Form.Item>
                  <Form.Item
                    name="email"
                    rules={[
                      { required: true, message: '请输入邮箱' },
                      { type: 'email', message: '请输入有效的邮箱地址' },
                    ]}
                  >
                    <Input
                      prefix={<MailOutlined className="text-gray-400" />}
                      placeholder="邮箱"
                      size="large"
                    />
                  </Form.Item>
                  <Form.Item
                    name="password"
                    rules={[
                      { required: true, message: '请输入密码' },
                      { min: 6, message: '密码至少6位' },
                    ]}
                  >
                    <Input.Password
                      prefix={<LockOutlined className="text-gray-400" />}
                      placeholder="密码（至少6位）"
                      size="large"
                    />
                  </Form.Item>
                  <Form.Item>
                    <Button
                      type="primary"
                      htmlType="submit"
                      size="large"
                      block
                      loading={isLoading}
                    >
                      注册
                    </Button>
                  </Form.Item>
                </Form>
              ),
            },
          ]}
        />

        <div className="text-center text-sm text-gray-400 mt-4">
          <p>登录即表示同意《用户协议》和《隐私政策》</p>
        </div>
      </Card>
    </div>
  );
};

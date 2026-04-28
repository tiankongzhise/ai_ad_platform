/**
 * 3步引导向导组件
 * 新用户注册后的配置引导
 */
import React, { useState, useEffect } from 'react';
import { Modal, Steps, Button, Form, Input, Select, Space, message, Spin } from 'antd';
import {
  ShopOutlined,
  CloudUploadOutlined,
  RocketOutlined,
  CheckCircleFilled,
} from '@ant-design/icons';
import { useOnboardingStore } from '@/store';
import { adAccountApi } from '@/api';

interface OnboardingWizardProps {
  open: boolean;
  onComplete: () => void;
  onSkip: () => void;
}

const STEP_ICONS = [
  <ShopOutlined key="step1" />,
  <CloudUploadOutlined key="step2" />,
  <RocketOutlined key="step3" />,
];

export const OnboardingWizard: React.FC<OnboardingWizardProps> = ({
  open,
  onComplete,
  onSkip,
}) => {
  const [form] = Form.useForm();
  const { currentStep, isLoading, status, fetchStatus, updateStep1, updateStep2, completeStep3 } = useOnboardingStore();
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);
  const [oauthLoading, setOauthLoading] = useState(false);

  useEffect(() => {
    if (open) {
      fetchStatus();
    }
  }, [open, fetchStatus]);

  // Step 1: 填写机构信息
  const handleStep1Submit = async () => {
    try {
      const values = await form.validateFields();
      await updateStep1({
        name: values.name,
        industry_sub_type: values.industry_type,
        main_product: values.main_product,
      });
      message.success('机构信息已保存');
    } catch (error) {
      // 表单验证失败
    }
  };

  // Step 2: 绑定广告账户
  const handleBindAdAccount = async (platform: string) => {
    setOauthLoading(true);
    try {
      let oauthUrlResponse;
      if (platform === 'juliang') {
        oauthUrlResponse = await adAccountApi.getJuliangOAuthUrl();
      } else {
        // 百度
        oauthUrlResponse = await adAccountApi.getBaiduOAuthUrl();
      }
      const { oauth_url } = oauthUrlResponse.data;
      // 打开 OAuth 授权页面
      window.open(oauth_url, '_blank', 'width=600,height=700');
    } catch (error) {
      message.error('获取授权链接失败，请稍后重试');
    } finally {
      setOauthLoading(false);
    }
  };

  const handleStep2Continue = async () => {
    if (selectedPlatforms.length === 0) {
      message.warning('请至少选择一个广告平台');
      return;
    }
    await updateStep2({ platforms: selectedPlatforms as any });
    message.success('广告账户绑定成功');
  };

  // Step 3: 导入CRM线索
  const handleStep3Complete = async () => {
    await completeStep3();
    onComplete();
    message.success('引导完成，开始使用 EduAdCRM！');
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="py-8">
            <h3 className="text-lg font-medium mb-6 text-center">
              欢迎使用 EduAdCRM！让我们先了解一下您的机构
            </h3>
            <Form
              form={form}
              layout="vertical"
              className="max-w-md mx-auto"
              initialValues={status?.step1_org_info}
            >
              <Form.Item
                name="name"
                label="机构名称"
                rules={[{ required: true, message: '请输入机构名称' }]}
              >
                <Input placeholder="例如：星海教育" />
              </Form.Item>
              <Form.Item
                name="industry_type"
                label="行业细分"
                rules={[{ required: true, message: '请选择行业细分' }]}
              >
                <Select placeholder="请选择">
                  <Select.Option value="k12">K12教育培训</Select.Option>
                  <Select.Option value="adult">成人职业教育</Select.Option>
                  <Select.Option value="language">语言培训</Select.Option>
                  <Select.Option value="study_abroad">留学咨询</Select.Option>
                  <Select.Option value="early_child">早教/幼教</Select.Option>
                  <Select.Option value="other">其他</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item
                name="main_product"
                label="主营课程/产品"
                rules={[{ required: true, message: '请输入主营课程/产品' }]}
              >
                <Input placeholder="例如：中小学数学辅导、雅思托福培训" />
              </Form.Item>
              <Form.Item className="mb-0">
                <Space className="w-full justify-end">
                  <Button onClick={onSkip}>跳过</Button>
                  <Button type="primary" onClick={handleStep1Submit} loading={isLoading}>
                    下一步
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </div>
        );

      case 2:
        return (
          <div className="py-8">
            <h3 className="text-lg font-medium mb-6 text-center">
              连接您的广告账户，开始追踪广告效果
            </h3>
            <div className="flex justify-center gap-8 mb-8">
              <button
                className={`flex flex-col items-center p-6 rounded-lg border-2 transition-all ${
                  selectedPlatforms.includes('juliang')
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-blue-300'
                }`}
                onClick={() => {
                  setSelectedPlatforms(prev =>
                    prev.includes('juliang')
                      ? prev.filter(p => p !== 'juliang')
                      : [...prev, 'juliang']
                  );
                }}
              >
                <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center mb-3">
                  <span className="text-3xl">🎵</span>
                </div>
                <span className="font-medium">巨量引擎（抖音）</span>
                {selectedPlatforms.includes('juliang') && (
                  <CheckCircleFilled className="text-blue-500 mt-2" />
                )}
              </button>
              <button
                className={`flex flex-col items-center p-6 rounded-lg border-2 transition-all ${
                  selectedPlatforms.includes('baidu')
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-blue-300'
                }`}
                onClick={() => {
                  setSelectedPlatforms(prev =>
                    prev.includes('baidu')
                      ? prev.filter(p => p !== 'baidu')
                      : [...prev, 'baidu']
                  );
                }}
              >
                <div className="w-16 h-16 rounded-full bg-blue-50 flex items-center justify-center mb-3">
                  <span className="text-3xl">🔍</span>
                </div>
                <span className="font-medium">百度营销</span>
                {selectedPlatforms.includes('baidu') && (
                  <CheckCircleFilled className="text-blue-500 mt-2" />
                )}
              </button>
            </div>
            <div className="text-center text-gray-500 mb-6">
              {selectedPlatforms.length === 0
                ? '请选择一个广告平台进行授权'
                : `已选择 ${selectedPlatforms.length} 个平台，点击授权按钮进行授权`}
            </div>
            <div className="flex justify-center gap-4 mb-8">
              <Button
                onClick={() => handleBindAdAccount('juliang')}
                loading={oauthLoading}
                disabled={!selectedPlatforms.includes('juliang')}
              >
                授权巨量引擎
              </Button>
              <Button
                onClick={() => handleBindAdAccount('baidu')}
                loading={oauthLoading}
                disabled={!selectedPlatforms.includes('baidu')}
              >
                授权百度营销
              </Button>
            </div>
            <div className="flex justify-end max-w-md mx-auto">
              <Space>
                <Button onClick={onSkip}>跳过此步</Button>
                <Button
                  type="primary"
                  onClick={handleStep2Continue}
                  loading={isLoading}
                >
                  已完成授权，继续
                </Button>
              </Space>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="py-8">
            <h3 className="text-lg font-medium mb-6 text-center">
              导入您的 CRM 线索，开启 ROI 分析
            </h3>
            <div className="max-w-md mx-auto text-center mb-8">
              <div className="w-24 h-24 rounded-full bg-green-50 flex items-center justify-center mx-auto mb-4">
                <CloudUploadOutlined className="text-4xl text-green-500" />
              </div>
              <p className="text-gray-500 mb-4">
                上传您的线索 Excel 文件，我们会自动识别字段并计算 ROI
              </p>
              <Button
                type="primary"
                size="large"
                onClick={() => {
                  // 导航到 CRM 导入页面
                  window.location.href = '/crm';
                }}
              >
                选择文件上传
              </Button>
            </div>
            <div className="flex justify-end max-w-md mx-auto">
              <Space>
                <Button onClick={onSkip}>跳过此步</Button>
                <Button type="primary" onClick={handleStep3Complete} loading={isLoading}>
                  完成引导
                </Button>
              </Space>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  if (isLoading && !status) {
    return (
      <Modal
        open={open}
        title={null}
        footer={null}
        closable={false}
        width={600}
      >
        <div className="flex items-center justify-center py-16">
          <Spin size="large" />
        </div>
      </Modal>
    );
  }

  return (
    <Modal
      open={open}
      title={null}
      footer={null}
      closable={false}
      width={700}
      centered
      className="onboarding-wizard-modal"
    >
      <Steps
        current={currentStep - 1}
        className="mb-8"
        items={[
          { title: '机构信息', icon: STEP_ICONS[0] },
          { title: '广告账户', icon: STEP_ICONS[1] },
          { title: '导入线索', icon: STEP_ICONS[2] },
        ]}
      />
      {renderStepContent()}
    </Modal>
  );
};

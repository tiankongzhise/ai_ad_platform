/**
 * 演示数据切换组件
 * Header 右上角切换开关
 */
import React from 'react';
import { Switch, Tooltip, Tag } from 'antd';
import { ExperimentOutlined } from '@ant-design/icons';
import { useDemoStore } from '@/store';

export const DemoDataToggle: React.FC = () => {
  const { isDemoMode, toggleDemoMode } = useDemoStore();

  return (
    <Tooltip title={isDemoMode ? '查看真实数据' : '查看演示数据（星海教育）'}>
      <div className="flex items-center gap-2">
        <ExperimentOutlined className={isDemoMode ? 'text-blue-500' : 'text-gray-400'} />
        <Switch
          checked={isDemoMode}
          onChange={toggleDemoMode}
          checkedChildren="演示"
          unCheckedChildren="真实"
          size="small"
        />
        {isDemoMode && (
          <Tag color="blue" className="m-0 text-xs">
            演示数据
          </Tag>
        )}
      </div>
    </Tooltip>
  );
};

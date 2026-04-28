/**
 * 导入进度浮窗组件
 * 可最小化的导入进度展示
 */
import React, { useState } from 'react';
import { Card, Progress, Button, Space, Tooltip } from 'antd';
import {
  CloseOutlined,
  MinusOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  LoadingOutlined,
} from '@ant-design/icons';
import { formatFileSize } from '@/utils';
import type { ImportProgress } from '@/types';

interface ProgressOverlayProps {
  progress: ImportProgress | null;
  isLoading: boolean;
  error: Error | null;
  onClose: () => void;
  onRetry?: () => void;
  filename?: string;
  fileSize?: number;
}

export const ProgressOverlay: React.FC<ProgressOverlayProps> = ({
  progress,
  isLoading,
  error,
  onClose,
  onRetry,
  filename,
  fileSize,
}) => {
  const [minimized, setMinimized] = useState(false);

  if (!progress && !isLoading && !error) {
    return null;
  }

  const getStatusIcon = () => {
    if (isLoading) return <LoadingOutlined className="text-blue-500" spin />;
    if (error) return <ExclamationCircleOutlined className="text-red-500" />;
    if (progress?.status === 'completed') return <CheckCircleOutlined className="text-green-500" />;
    if (progress?.status === 'failed') return <ExclamationCircleOutlined className="text-red-500" />;
    return <LoadingOutlined className="text-blue-500" />;
  };

  const getStatusText = () => {
    if (error) return '导入失败';
    if (!progress) return '准备中...';
    switch (progress.status) {
      case 'pending':
        return '等待处理...';
      case 'processing':
        return `处理中 (${progress.progress}%)`;
      case 'completed':
        return '导入完成';
      case 'failed':
        return '导入失败';
      default:
        return '处理中...';
    }
  };

  const getProgressPercent = () => {
    if (!progress) return 0;
    return progress.progress || Math.round((progress.processed_rows / progress.total_rows) * 100);
  };

  if (minimized) {
    return (
      <Tooltip title="点击展开" placement="left">
        <Card
          className="fixed bottom-4 right-4 shadow-lg cursor-pointer"
          style={{ width: 48, height: 48 }}
          styles={{ body: { padding: 0, height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' } }}
          onClick={() => setMinimized(false)}
        >
          {getStatusIcon()}
        </Card>
      </Tooltip>
    );
  }

  return (
    <Card
      className="fixed bottom-4 right-4 shadow-lg"
      style={{ width: 360 }}
      styles={{ body: { padding: '16px' } }}
      title={
        <div className="flex items-center justify-between">
          <Space>
            {getStatusIcon()}
            <span>{getStatusText()}</span>
          </Space>
          <Space size={4}>
            <Button
              type="text"
              size="small"
              icon={<MinusOutlined />}
              onClick={() => setMinimized(true)}
            />
            <Button
              type="text"
              size="small"
              icon={<CloseOutlined />}
              onClick={onClose}
            />
          </Space>
        </div>
      }
    >
      {/* 文件信息 */}
      {filename && (
        <div className="mb-3">
          <div className="text-sm text-gray-500">正在导入</div>
          <div className="font-medium truncate">{filename}</div>
          {fileSize && (
            <div className="text-xs text-gray-400">{formatFileSize(fileSize)}</div>
          )}
        </div>
      )}

      {/* 进度条 */}
      {progress && (
        <div className="mb-3">
          <Progress
            percent={getProgressPercent()}
            status={progress.status === 'failed' ? 'exception' : progress.status === 'completed' ? 'success' : 'active'}
            strokeColor={progress.status === 'failed' ? '#ff4d4f' : '#0ea5e9'}
          />
          <div className="flex justify-between text-xs text-gray-500">
            <span>
              {progress.processed_rows} / {progress.total_rows} 行
            </span>
            {progress.message && <span>{progress.message}</span>}
          </div>
        </div>
      )}

      {/* 错误信息 */}
      {error && (
        <div className="mb-3 p-2 bg-red-50 rounded text-red-600 text-sm">
          {error.message}
        </div>
      )}

      {/* 操作按钮 */}
      {(error || progress?.status === 'completed') && (
        <div className="flex justify-end">
          {error && onRetry && (
            <Button
              size="small"
              icon={<ReloadOutlined />}
              onClick={onRetry}
            >
              重试
            </Button>
          )}
        </div>
      )}
    </Card>
  );
};

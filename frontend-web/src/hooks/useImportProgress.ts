/**
 * 导入进度 Hook
 * 轮询获取导入任务进度
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { crmApi } from '@/api';
import type { ImportProgress } from '@/types';

interface UseImportProgressOptions {
  /** 轮询间隔（毫秒） */
  interval?: number;
  /** 最大轮询次数 */
  maxAttempts?: number;
  /** 轮询完成后的回调 */
  onComplete?: (progress: ImportProgress) => void;
  /** 轮询失败的回调 */
  onError?: (error: Error) => void;
}

interface UseImportProgressResult {
  progress: ImportProgress | null;
  isLoading: boolean;
  error: Error | null;
  startPolling: (taskId: string) => void;
  stopPolling: () => void;
}

export function useImportProgress(options: UseImportProgressOptions = {}): UseImportProgressResult {
  const {
    interval = 2000,
    maxAttempts = 150, // 最多轮询 5 分钟
    onComplete,
    onError,
  } = options;

  const [progress, setProgress] = useState<ImportProgress | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const taskIdRef = useRef<string | null>(null);
  const attemptsRef = useRef(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    taskIdRef.current = null;
    attemptsRef.current = 0;
  }, []);

  const fetchProgress = useCallback(async () => {
    if (!taskIdRef.current) return;

    try {
      const response = await crmApi.getUploadProgress(taskIdRef.current);
      const data = response.data;
      
      setProgress(data);
      setIsLoading(false);

      // 检查是否完成
      if (data.status === 'completed' || data.status === 'failed') {
        stopPolling();
        if (data.status === 'completed' && onComplete) {
          onComplete(data);
        }
        return;
      }

      // 检查是否超过最大次数
      attemptsRef.current += 1;
      if (attemptsRef.current >= maxAttempts) {
        stopPolling();
        const err = new Error('导入超时，请稍后查看结果');
        setError(err);
        if (onError) onError(err);
      }
    } catch (err) {
      setError(err as Error);
      if (onError) onError(err as Error);
    }
  }, [maxAttempts, onComplete, onError, stopPolling]);

  const startPolling = useCallback((taskId: string) => {
    stopPolling();
    taskIdRef.current = taskId;
    attemptsRef.current = 0;
    setIsLoading(true);
    setError(null);

    // 立即获取一次
    fetchProgress();

    // 开始轮询
    intervalRef.current = setInterval(fetchProgress, interval);
  }, [fetchProgress, interval, stopPolling]);

  // 组件卸载时停止轮询
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  return {
    progress,
    isLoading,
    error,
    startPolling,
    stopPolling,
  };
}

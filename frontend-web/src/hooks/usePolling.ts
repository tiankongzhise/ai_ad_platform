/**
 * 通用轮询 Hook
 */
import { useState, useEffect, useCallback, useRef } from 'react';

interface UsePollingOptions<T> {
  /** 轮询间隔（毫秒） */
  interval?: number;
  /** 是否立即获取数据 */
  immediate?: boolean;
  /** 最大轮询次数，0 表示不限制 */
  maxAttempts?: number;
}

interface UsePollingResult<T> {
  data: T | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
  stopPolling: () => void;
  isPolling: boolean;
}

export function usePolling<T>(
  fetcher: () => Promise<T>,
  options: UsePollingOptions<T> = {}
): UsePollingResult<T> {
  const {
    interval = 5000,
    immediate = true,
    maxAttempts = 0,
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  const fetcherRef = useRef(fetcher);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const attemptsRef = useRef(0);
  const isActiveRef = useRef(false);

  fetcherRef.current = fetcher;

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    isActiveRef.current = false;
    setIsPolling(false);
  }, []);

  const fetchData = useCallback(async () => {
    try {
      const result = await fetcherRef.current();
      setData(result);
      setError(null);
      
      // 检查是否达到最大次数
      if (maxAttempts > 0) {
        attemptsRef.current += 1;
        if (attemptsRef.current >= maxAttempts) {
          stopPolling();
        }
      }
    } catch (err) {
      setError(err as Error);
    }
  }, [maxAttempts, stopPolling]);

  const refetch = useCallback(async () => {
    setIsLoading(true);
    await fetchData();
    setIsLoading(false);
  }, [fetchData]);

  useEffect(() => {
    isActiveRef.current = true;
    
    if (immediate) {
      fetchData();
    }

    setIsPolling(true);
    intervalRef.current = setInterval(() => {
      if (isActiveRef.current) {
        fetchData();
      }
    }, interval);

    return () => {
      stopPolling();
    };
  }, [fetchData, immediate, interval, stopPolling]);

  return {
    data,
    isLoading,
    error,
    refetch,
    stopPolling,
    isPolling,
  };
}

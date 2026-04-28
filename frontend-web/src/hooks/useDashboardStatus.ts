/**
 * 仪表盘状态 Hook
 * 获取仪表盘数据状态，决定展示哪种空态
 */
import { useState, useEffect, useCallback } from 'react';
import { analyticsApi } from '@/api';
import type { DashboardStatus, DashboardStatusResponse } from '@/types';

interface UseDashboardStatusResult {
  status: DashboardStatus | null;
  response: DashboardStatusResponse | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

export function useDashboardStatus(): UseDashboardStatusResult {
  const [status, setStatus] = useState<DashboardStatus | null>(null);
  const [response, setResponse] = useState<DashboardStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchStatus = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const res = await analyticsApi.getDashboardStatus();
      setResponse(res.data);
      setStatus(res.data.status);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  return {
    status,
    response,
    isLoading,
    error,
    refetch: fetchStatus,
  };
}

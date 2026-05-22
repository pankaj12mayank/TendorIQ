/**
 * Platform-wide analytics for the super-admin console only.
 * Tenant usage lives at `/api/v1/billing/usage/*` (see `use-usage.ts`).
 */
import { useCallback, useState, useEffect, useRef } from 'react';
import { api } from '@/lib/api-client';
import { useAnalyticsStore } from '@/components/admin/store';
import { UsageMetric, AnalyticsCard } from '@/components/admin/types';
import { ANALYTICS_CARDS } from '@/components/admin/constants';

interface UseAnalyticsApiReturn {
  metrics: UsageMetric[];
  cards: AnalyticsCard[];
  isLoading: boolean;
  timeRange: string;
  setTimeRange: (range: string) => void;
  fetchMetrics: () => Promise<void>;
  exportReport: (format: 'csv' | 'json' | 'pdf') => Promise<void>;
  getMetricByDate: (date: string) => UsageMetric | undefined;
  getTotal: (field: keyof UsageMetric) => number;
}

export function useAnalyticsApi(): UseAnalyticsApiReturn {
  const { metrics: storeMetrics, setMetrics } = useAnalyticsStore();
  const [allMetrics, setAllMetrics] = useState<UsageMetric[]>([]);
  const [cards, setCards] = useState<AnalyticsCard[]>(ANALYTICS_CARDS);
  const [isLoading, setLoading] = useState(false);
  const [isError, setIsError] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState('7d');

  const fetchMetrics = useCallback(async () => {
    setLoading(true);
    setIsError(false);
    setError(null);
    try {
      const res = await api.get<{
        scope?: string;
        dataSource?: string;
        totalUsers: number;
        apiCallsToday: number;
        activeJobs: number;
        errorRate: number;
        monthlyCost: number;
        usage: UsageMetric[];
      }>('/api/v1/admin/platform/analytics/summary');

      setMetrics({
        totalUsers: res.totalUsers,
        activeDocuments: res.activeJobs,
        apiCallsToday: res.apiCallsToday,
        monthlyCost: res.monthlyCost,
      });

      setCards([
        { title: 'Total Users', value: String(res.totalUsers), change: 0, changeType: 'increase', trend: 'up' },
        { title: 'API Calls Today', value: String(res.apiCallsToday), change: 0, changeType: 'increase', trend: 'up' },
        { title: 'Active Jobs', value: String(res.activeJobs), change: 0, changeType: 'increase', trend: 'up' },
        { title: 'Monthly Cost', value: `$${res.monthlyCost}`, change: 0, changeType: 'decrease', trend: 'down' },
      ]);

      setAllMetrics(res.usage?.length ? res.usage : []);
    } catch (err) {
      setIsError(true);
      setError(err instanceof Error ? err.message : 'Failed to fetch analytics');
    } finally {
      setLoading(false);
    }
  }, [setMetrics]);

  useEffect(() => {
    void fetchMetrics();
  }, [fetchMetrics]);

  const exportReport = useCallback(
    async (format: 'csv' | 'json' | 'pdf') => {
      setLoading(true);
      try {
        const data = JSON.stringify({ metrics: allMetrics, cards, summary: storeMetrics }, null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `analytics-report.${format === 'pdf' ? 'json' : format}`;
        a.click();
        URL.revokeObjectURL(url);
      } finally {
        setLoading(false);
      }
    },
    [allMetrics, cards, storeMetrics]
  );

  const getMetricByDate = useCallback(
    (date: string) => allMetrics.find((m) => m.date === date),
    [allMetrics]
  );

  const getTotal = useCallback(
    (field: keyof UsageMetric) =>
      allMetrics.reduce(
        (sum, m) => sum + (typeof m[field] === 'number' ? (m[field] as number) : 0),
        0
      ),
    [allMetrics]
  );

  return {
    metrics: allMetrics,
    cards,
    isLoading,
    timeRange,
    setTimeRange,
    fetchMetrics,
    exportReport,
    getMetricByDate,
    getTotal,
  };
}

interface UseRealtimeMetricsReturn {
  apiCalls: number;
  activeJobs: number;
  errorRate: number;
  avgResponseTime: number;
  subscribe: () => void;
  unsubscribe: () => void;
}

export function useRealtimeMetrics(): UseRealtimeMetricsReturn {
  const { metrics } = useAnalyticsStore();
  const [activeJobs, setActiveJobs] = useState(0);
  const [errorRate, setErrorRate] = useState(0);
  const [avgResponseTime, setAvgResponseTime] = useState(0);
  const intervalRef = useRef<number | undefined>(undefined);

  const subscribe = useCallback(() => {
    intervalRef.current = window.setInterval(async () => {
      try {
        const res = await api.get<{
          activeJobs: number;
          errorRate: number;
          avgResponseTime: number;
        }>('/api/v1/admin/platform/analytics/summary');
        setActiveJobs(res.activeJobs);
        setErrorRate(res.errorRate);
        setAvgResponseTime(res.avgResponseTime);
      } catch {}
    }, 30000);
  }, []);

  const unsubscribe = useCallback(() => {
    if (intervalRef.current !== undefined) {
      clearInterval(intervalRef.current);
      intervalRef.current = undefined;
    }
  }, []);

  useEffect(() => {
    return () => unsubscribe();
  }, [unsubscribe]);

  return {
    apiCalls: metrics.apiCallsToday,
    activeJobs,
    errorRate,
    avgResponseTime,
    subscribe,
    unsubscribe,
  };
}

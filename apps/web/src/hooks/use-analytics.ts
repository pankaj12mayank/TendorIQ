/**
 * Platform-wide analytics for the super-admin console only.
 * Tenant usage lives at `/api/v1/billing/usage/*` (see `use-usage.ts`).
 */
import { useCallback, useState, useEffect, useRef } from 'react';
import { api } from '@/lib/api-client';
import {
  parsePlatformAnalyticsSummary,
  type PlatformAnalyticsSummary,
  type PlatformHealthComponent,
  type PlatformQueueStats,
} from '@/lib/admin-platform-api';
import { useAnalyticsStore } from '@/components/admin/store';
import { UsageMetric, AnalyticsCard } from '@/components/admin/types';
import { ANALYTICS_CARDS } from '@/components/admin/constants';

interface UseAnalyticsApiReturn {
  metrics: UsageMetric[];
  cards: AnalyticsCard[];
  isLoading: boolean;
  isError: boolean;
  error: string | null;
  timeRange: string;
  setTimeRange: (range: string) => void;
  fetchMetrics: () => Promise<void>;
  exportReport: (format: 'csv' | 'json') => Promise<void>;
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
      const raw = await api.get<unknown>('/api/v1/admin/platform/analytics/summary');
      const res = parsePlatformAnalyticsSummary(raw);

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
    async (format: 'csv' | 'json') => {
      setLoading(true);
      try {
        const payload = { metrics: allMetrics, cards, summary: storeMetrics };
        let body: string;
        let mime: string;
        if (format === 'csv') {
          const header = 'date,apiCalls,documentsProcessed,tokensUsed,cost\n';
          const rows = allMetrics
            .map(
              (m) =>
                `${m.date},${m.apiCalls ?? 0},${m.documentsProcessed ?? 0},${m.tokensUsed ?? 0},${m.cost ?? 0}`
            )
            .join('\n');
          body = header + rows;
          mime = 'text/csv';
        } else {
          body = JSON.stringify(payload, null, 2);
          mime = 'application/json';
        }
        const blob = new Blob([body], { type: mime });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `analytics-report.${format}`;
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
    isError,
    error,
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
  queueStats: PlatformQueueStats | null;
  systemHealth: PlatformHealthComponent[];
  isLoading: boolean;
  refresh: () => Promise<void>;
  subscribe: () => void;
  unsubscribe: () => void;
}

export function useRealtimeMetrics(): UseRealtimeMetricsReturn {
  const { metrics } = useAnalyticsStore();
  const [summary, setSummary] = useState<PlatformAnalyticsSummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const intervalRef = useRef<number | undefined>(undefined);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    try {
      const raw = await api.get<unknown>('/api/v1/admin/platform/analytics/summary');
      setSummary(parsePlatformAnalyticsSummary(raw));
    } catch {
      /* keep last snapshot */
    } finally {
      setIsLoading(false);
    }
  }, []);

  const subscribe = useCallback(() => {
    void refresh();
    intervalRef.current = window.setInterval(() => {
      void refresh();
    }, 30000);
  }, [refresh]);

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
    apiCalls: summary?.apiCallsToday ?? metrics.apiCallsToday,
    activeJobs: summary?.activeJobs ?? 0,
    errorRate: summary?.errorRate ?? 0,
    avgResponseTime: summary?.avgResponseTime ?? 0,
    queueStats: summary?.queueStats ?? null,
    systemHealth: summary?.systemHealth?.components ?? [],
    isLoading,
    refresh,
    subscribe,
    unsubscribe,
  };
}

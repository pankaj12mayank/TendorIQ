import { useCallback, useState, useEffect } from 'react';
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
  const [timeRange, setTimeRange] = useState('7d');

  const fetchMetrics = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get<{
        totalUsers: number;
        apiCallsToday: number;
        activeJobs: number;
        errorRate: number;
        monthlyCost: number;
        usage: UsageMetric[];
      }>('/api/v1/admin/platform/analytics/summary');

      setMetrics({
        totalUsers: res.totalUsers,
        activeDocuments: 0,
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

  return {
    apiCalls: metrics.apiCallsToday,
    activeJobs: 0,
    errorRate: 0,
    avgResponseTime: 0,
    subscribe: () => {},
    unsubscribe: () => {},
  };
}

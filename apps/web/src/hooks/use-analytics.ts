import { useCallback, useState } from 'react';
import { useAnalyticsStore } from '@/components/admin/store';
import { UsageMetric, AnalyticsCard } from '@/components/admin/types';
import { MOCK_USAGE_METRICS, ANALYTICS_CARDS } from '@/components/admin/constants';

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
  const { metrics, sparklineData, setMetrics } = useAnalyticsStore();
  const [allMetrics] = useState<UsageMetric[]>(MOCK_USAGE_METRICS);
  const [cards] = useState<AnalyticsCard[]>(ANALYTICS_CARDS);
  const [isLoading, setLoading] = useState(false);
  const [timeRange, setTimeRange] = useState('7d');

  const fetchMetrics = useCallback(async () => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    setLoading(false);
  }, []);

  const exportReport = useCallback(async (format: 'csv' | 'json' | 'pdf') => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    const data = format === 'json' 
      ? JSON.stringify({ metrics: allMetrics, cards }, null, 2)
      : JSON.stringify({ metrics: allMetrics, cards });
    
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analytics-report.${format}`;
    a.click();
    URL.revokeObjectURL(url);
    
    setLoading(false);
  }, [allMetrics]);

  const getMetricByDate = useCallback((date: string) => {
    return allMetrics.find(m => m.date === date);
  }, [allMetrics]);

  const getTotal = useCallback((field: keyof UsageMetric) => {
    return allMetrics.reduce((sum, m) => sum + (typeof m[field] === 'number' ? m[field] as number : 0), 0);
  }, [allMetrics]);

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
  const [apiCalls, setApiCalls] = useState(2150);
  const [activeJobs, setActiveJobs] = useState(12);
  const [errorRate, setErrorRate] = useState(0.5);
  const [avgResponseTime, setAvgResponseTime] = useState(245);
  
  const subscribe = useCallback(() => {
    const interval = setInterval(() => {
      setApiCalls(prev => prev + Math.floor(Math.random() * 10) - 3);
      setActiveJobs(prev => Math.max(0, prev + Math.floor(Math.random() * 3) - 1));
      setErrorRate(prev => Math.max(0, Math.min(5, prev + (Math.random() - 0.5) * 0.2)));
      setAvgResponseTime(prev => Math.max(100, Math.min(500, prev + Math.floor(Math.random() * 40) - 20)));
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);

  const unsubscribe = useCallback(() => {
  }, []);

  return {
    apiCalls,
    activeJobs,
    errorRate,
    avgResponseTime,
    subscribe,
    unsubscribe,
  };
}
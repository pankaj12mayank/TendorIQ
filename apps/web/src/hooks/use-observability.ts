'use client';

import { useCallback, useState } from 'react';
import { api } from '@/lib/api-client';
import {
  parseObservabilitySummary,
  parseTrendResponse,
  type ObservabilitySummary,
  type TrendPoint,
} from '@/lib/observability-api';

export function useObservability() {
  const [summary, setSummary] = useState<ObservabilitySummary | null>(null);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [isLoading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<unknown>('/api/v1/observability/metrics/summary');
      setSummary(parseObservabilitySummary(res));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load observability metrics');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchTrends = useCallback(
    async (metricType: 'api' | 'queue' | 'ai' | 'processing', days = 7) => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.get<unknown>('/api/v1/observability/trends', {
          params: { metric_type: metricType, days },
        });
        const parsed = parseTrendResponse(res);
        setTrends(parsed.data);
        return parsed;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load metric trends');
        throw err;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return {
    summary,
    trends,
    isLoading,
    error,
    fetchSummary,
    fetchTrends,
  };
}

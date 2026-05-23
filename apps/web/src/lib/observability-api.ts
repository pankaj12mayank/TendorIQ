import { unwrapData } from './api-envelope';

export interface ObservabilityApiMetrics {
  total_requests: number;
  error_rate: number;
  avg_response_time_ms: number;
}

export interface ObservabilityQueueMetrics {
  total_jobs: number;
  active_jobs: number;
  failure_rate: number;
}

export interface ObservabilityAiMetrics {
  total_requests: number;
  total_cost: number;
  total_tokens: number;
}

export interface ObservabilityProcessingMetrics {
  documents_processed: number;
  success_rate: number;
}

export interface ObservabilitySummary {
  api: ObservabilityApiMetrics;
  queue: ObservabilityQueueMetrics;
  ai: ObservabilityAiMetrics;
  processing: ObservabilityProcessingMetrics;
}

export interface TrendPoint {
  date: string;
  value?: number;
  input?: number;
  output?: number;
  cost?: number;
}

export function parseObservabilitySummary(payload: unknown): ObservabilitySummary {
  const data = unwrapData<ObservabilitySummary>(payload as { data?: ObservabilitySummary });
  if (data?.api) return data;
  return (payload as ObservabilitySummary) ?? {
    api: { total_requests: 0, error_rate: 0, avg_response_time_ms: 0 },
    queue: { total_jobs: 0, active_jobs: 0, failure_rate: 0 },
    ai: { total_requests: 0, total_cost: 0, total_tokens: 0 },
    processing: { documents_processed: 0, success_rate: 0 },
  };
}

export function parseTrendResponse(payload: unknown): { metric: string; data: TrendPoint[] } {
  const body = (payload ?? {}) as { metric?: string; data?: TrendPoint[] };
  return {
    metric: body.metric ?? 'unknown',
    data: body.data ?? [],
  };
}

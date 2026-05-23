import { describe, expect, it } from 'vitest';

import { parseObservabilitySummary, parseTrendResponse } from '../observability-api';

describe('observability-api', () => {
  it('unwraps metrics summary envelope', () => {
    const summary = parseObservabilitySummary({
      success: true,
      data: {
        api: { total_requests: 10, error_rate: 2.5, avg_response_time_ms: 0 },
        queue: { total_jobs: 5, active_jobs: 1, failure_rate: 2.5 },
        ai: { total_requests: 10, total_cost: 1.2, total_tokens: 500 },
        processing: { documents_processed: 3, success_rate: 95 },
      },
    });
    expect(summary.queue.active_jobs).toBe(1);
    expect(summary.ai.total_tokens).toBe(500);
  });

  it('parses trend series', () => {
    const trend = parseTrendResponse({
      metric: 'api_requests',
      data: [{ date: '2026-05-01', value: 12 }],
    });
    expect(trend.metric).toBe('api_requests');
    expect(trend.data[0].value).toBe(12);
  });
});

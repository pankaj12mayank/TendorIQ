import { describe, expect, it } from 'vitest';

import {
  parsePlatformAnalyticsSummary,
  parsePlatformAuditLogsResponse,
  parsePlatformQueueStats,
  parsePlatformUsersResponse,
} from '../admin-platform-api';

describe('admin-platform-api', () => {
  it('parses analytics summary with queue and health', () => {
    const summary = parsePlatformAnalyticsSummary({
      totalUsers: 10,
      apiCallsToday: 42,
      activeJobs: 3,
      errorRate: 1.5,
      avgResponseTime: 0,
      monthlyCost: 99,
      usage: [{ date: '2026-05-01', apiCalls: 5, documentsProcessed: 1, tokensUsed: 100, cost: 0.1 }],
      queueStats: { pending: 1, processing: 2, completed: 10, failed: 0, total: 13, healthPercent: 92 },
      systemHealth: {
        status: 'healthy',
        components: [{ name: 'API Server', status: 'healthy', uptime: 99.9 }],
      },
    });
    expect(summary.totalUsers).toBe(10);
    expect(summary.queueStats?.pending).toBe(1);
    expect(summary.systemHealth?.components[0]?.name).toBe('API Server');
  });

  it('unwraps envelope users response', () => {
    const { users, total } = parsePlatformUsersResponse({
      data: { users: [{ id: '1', email: 'a@b.c' }], total: 1 },
    });
    expect(users).toHaveLength(1);
    expect(total).toBe(1);
  });

  it('parses platform audit logs list', () => {
    const logs = parsePlatformAuditLogsResponse({
      logs: [
        {
          id: 'x',
          action: 'update',
          action_type: 'admin_action',
          resource_type: 'user',
          user_name: 'Ada',
          created_at: '2026-05-01T00:00:00Z',
        },
      ],
    });
    expect(logs[0]?.userName).toBe('Ada');
    expect(logs[0]?.action).toBe('update');
  });

  it('computes queue health when omitted', () => {
    const stats = parsePlatformQueueStats({
      pending: 2,
      processing: 1,
      completed: 7,
      failed: 0,
      total: 10,
    });
    expect(stats.healthPercent).toBe(80);
  });
});

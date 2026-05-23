/** Canonical super-admin platform API paths (contract with OpenAPI). */
export const ADMIN_PLATFORM_PATHS = {
  users: '/api/v1/admin/platform/users',
  billing: '/api/v1/admin/platform/billing',
  aiProviders: '/api/v1/admin/platform/ai-providers',
  aiProviderTest: (id: string) => `/api/v1/admin/platform/ai-providers/${id}/test`,
  queueJobs: '/api/v1/admin/platform/queue/jobs',
  queueJobRetry: (id: string) => `/api/v1/admin/platform/queue/jobs/${id}/retry`,
  queueJobCancel: (id: string) => `/api/v1/admin/platform/queue/jobs/${id}/cancel`,
  queueJobPause: (id: string) => `/api/v1/admin/platform/queue/jobs/${id}/pause`,
  queueJobResume: (id: string) => `/api/v1/admin/platform/queue/jobs/${id}/resume`,
  failedJobs: '/api/v1/admin/platform/failed-jobs',
  failedJob: (id: string) => `/api/v1/admin/platform/failed-jobs/${id}`,
  analyticsSummary: '/api/v1/admin/platform/analytics/summary',
  platformHealth: '/api/v1/admin/platform/health',
  quotaOverrides: '/api/v1/admin/platform/quota-overrides',
  auditLogs: '/api/v1/admin/platform/audit-logs',
  auditLogsExport: '/api/v1/admin/platform/audit-logs/export',
} as const;

export const PROMPTS_PATHS = {
  list: '/api/v1/prompts',
  item: (id: string) => `/api/v1/prompts/${id}`,
} as const;

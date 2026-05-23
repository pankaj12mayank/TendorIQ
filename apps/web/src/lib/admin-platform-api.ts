import type {
  User,
  AIProvider,
  QueueJob,
  FailedJob,
  AuditLogEntry,
  UsageMetric,
} from '../components/admin/types';
import { unwrapData } from './api-envelope';

export interface PlatformQueueStats {
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  cancelled?: number;
  total: number;
  healthPercent: number;
}

export interface PlatformHealthComponent {
  name: string;
  status: 'healthy' | 'degraded' | 'unhealthy' | string;
  uptime: number;
}

export interface PlatformAnalyticsSummary {
  dataSource?: string;
  scope?: string;
  totalUsers: number;
  apiCallsToday: number;
  activeJobs: number;
  errorRate: number;
  avgResponseTime: number;
  monthlyCost: number;
  usage: UsageMetric[];
  queueStats?: PlatformQueueStats;
  systemHealth?: {
    status: string;
    components: PlatformHealthComponent[];
    failedJobs?: number;
  };
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function num(value: unknown, fallback = 0): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

export function parsePlatformQueueStats(payload: unknown): PlatformQueueStats {
  const body = asRecord(unwrapData(payload) ?? payload);
  const pending = num(body.pending);
  const processing = num(body.processing);
  const completed = num(body.completed);
  const failed = num(body.failed);
  const cancelled = num(body.cancelled);
  const total = num(body.total, pending + processing + completed + failed + cancelled);
  const healthPercent = num(
    body.healthPercent,
    total > 0 ? Math.round(((completed + processing) / total) * 1000) / 10 : 100
  );
  return { pending, processing, completed, failed, cancelled, total, healthPercent };
}

export function parsePlatformHealth(payload: unknown): PlatformAnalyticsSummary['systemHealth'] {
  const body = asRecord(unwrapData(payload) ?? payload);
  const componentsRaw = body.components;
  const components: PlatformHealthComponent[] = Array.isArray(componentsRaw)
    ? componentsRaw.map((row) => {
        const c = asRecord(row);
        return {
          name: String(c.name ?? 'Component'),
          status: String(c.status ?? 'unknown'),
          uptime: num(c.uptime),
        };
      })
    : [];
  return {
    status: String(body.status ?? 'unknown'),
    components,
    failedJobs: num(body.failedJobs),
  };
}

export function parsePlatformAnalyticsSummary(payload: unknown): PlatformAnalyticsSummary {
  const body = asRecord(unwrapData(payload) ?? payload);
  const usageRaw = body.usage;
  const usage: UsageMetric[] = Array.isArray(usageRaw)
    ? usageRaw.map((row) => {
        const u = asRecord(row);
        return {
          date: String(u.date ?? ''),
          apiCalls: num(u.apiCalls ?? u.api_calls),
          documentsProcessed: num(u.documentsProcessed ?? u.documents_processed),
          tokensUsed: num(u.tokensUsed ?? u.tokens_used),
          cost: num(u.cost),
        };
      })
    : [];

  return {
    dataSource: body.dataSource as string | undefined,
    scope: body.scope as string | undefined,
    totalUsers: num(body.totalUsers),
    apiCallsToday: num(body.apiCallsToday),
    activeJobs: num(body.activeJobs),
    errorRate: num(body.errorRate),
    avgResponseTime: num(body.avgResponseTime),
    monthlyCost: num(body.monthlyCost),
    usage,
    queueStats: body.queueStats ? parsePlatformQueueStats(body.queueStats) : undefined,
    systemHealth: body.systemHealth ? parsePlatformHealth(body.systemHealth) : undefined,
  };
}

export function parsePlatformUsersResponse(payload: unknown): { users: User[]; total: number } {
  const body = asRecord(unwrapData(payload) ?? payload);
  const usersRaw = body.users;
  const users = Array.isArray(usersRaw) ? (usersRaw as User[]) : [];
  return { users, total: num(body.total, users.length) };
}

export function parsePlatformProvidersResponse(payload: unknown): AIProvider[] {
  const body = asRecord(unwrapData(payload) ?? payload);
  const list = body.providers;
  return Array.isArray(list) ? (list as AIProvider[]) : [];
}

export function parsePlatformQueueJobsResponse(payload: unknown): QueueJob[] {
  const body = asRecord(unwrapData(payload) ?? payload);
  const list = body.jobs;
  return Array.isArray(list) ? (list as QueueJob[]) : [];
}

export function parsePlatformFailedJobsResponse(payload: unknown): FailedJob[] {
  const body = asRecord(unwrapData(payload) ?? payload);
  const list = body.jobs;
  return Array.isArray(list) ? (list as FailedJob[]) : [];
}

export function parsePlatformAuditLogsResponse(payload: unknown): AuditLogEntry[] {
  const body = asRecord(unwrapData(payload) ?? payload);
  const logsRaw = body.logs ?? body;
  if (!Array.isArray(logsRaw)) return [];
  return logsRaw.map((row) => mapAuditLog(row as Record<string, unknown>));
}

export function mapAuditLog(row: Record<string, unknown>): AuditLogEntry {
  return {
    id: String(row.id),
    userId: String(row.user_id ?? row.userId ?? ''),
    userName: String(row.user_name ?? row.userName ?? row.user_email ?? 'Unknown'),
    userRole: String(row.user_role ?? row.userRole ?? 'user'),
    action: String(row.action),
    resource: String(row.resource_type ?? row.resource ?? ''),
    resourceId: row.resource_id != null ? String(row.resource_id) : undefined,
    details: String(
      row.changes ? JSON.stringify(row.changes) : row.resource_name ?? row.action
    ),
    ipAddress: String(row.ip_address ?? ''),
    userAgent: String(row.user_agent ?? ''),
    timestamp: String(row.created_at ?? row.timestamp ?? ''),
    actionType: String(row.action_type ?? 'admin_action'),
    previousState:
      row.old_values && typeof row.old_values === 'object'
        ? (row.old_values as Record<string, unknown>)
        : undefined,
    newState:
      row.new_values && typeof row.new_values === 'object'
        ? (row.new_values as Record<string, unknown>)
        : undefined,
  };
}

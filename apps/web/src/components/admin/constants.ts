import { Role } from './types';
import { ROLE_PERMISSIONS_MATRIX } from '@/lib/permissions';

const ROLE_LABELS: Record<string, { name: string; description: string }> = {
  super_admin: { name: 'Super Admin', description: 'Full platform access' },
  owner: { name: 'Owner', description: 'Tenant owner' },
  admin: { name: 'Admin', description: 'Administrative access' },
  manager: { name: 'Manager', description: 'Team management' },
  analyst: { name: 'Analyst', description: 'Analysis access' },
  member: { name: 'Member', description: 'Standard member access' },
  viewer: { name: 'Viewer', description: 'Read-only access' },
};

/** Role options for admin user forms — derived from the shared permission matrix. */
export const ADMIN_ROLE_OPTIONS: Role[] = Object.entries(ROLE_PERMISSIONS_MATRIX).map(
  ([id, permissions]) => {
    const meta = ROLE_LABELS[id] ?? {
      name: id.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
      description: `${id} role`,
    };
    return {
      id,
      name: meta.name,
      description: meta.description,
      permissions: [...permissions],
      userCount: 0,
    };
  }
);

/** @deprecated Use ADMIN_ROLE_OPTIONS */
export const MOCK_ROLES = ADMIN_ROLE_OPTIONS;

export const ANALYTICS_CARDS = [
  { title: 'Total Users', value: '—', change: 0, changeType: 'increase' as const, trend: 'up' as const },
  { title: 'Active Documents', value: '—', change: 0, changeType: 'increase' as const, trend: 'up' as const },
  { title: 'API Calls Today', value: '—', change: 0, changeType: 'increase' as const, trend: 'up' as const },
  { title: 'Monthly Cost', value: '—', change: 0, changeType: 'decrease' as const, trend: 'down' as const },
];

export const ADMIN_MODULES = [
  { id: 'users', label: 'Users', icon: 'users', description: 'Manage users and roles' },
  { id: 'billing', label: 'Billing', icon: 'credit-card', description: 'Subscriptions and invoices' },
  { id: 'ai_settings', label: 'AI Settings', icon: 'cpu', description: 'AI providers and models' },
  { id: 'prompts', label: 'Prompts', icon: 'message-square', description: 'Prompt templates' },
  { id: 'queue', label: 'Queue', icon: 'list', description: 'Job queue monitoring' },
  { id: 'audit', label: 'Audit Logs', icon: 'file-text', description: 'System audit trail' },
  { id: 'analytics', label: 'Analytics', icon: 'bar-chart-2', description: 'Usage analytics' },
  { id: 'failed_jobs', label: 'Failed Jobs', icon: 'alert-circle', description: 'Failed job management' },
  { id: 'email_system', label: 'Email System', icon: 'mail', description: 'Transactional email automation' },
] as const;

export const ROLE_COLORS = {
  super_admin: 'bg-purple-100 text-purple-800',
  admin: 'bg-blue-100 text-blue-800',
  manager: 'bg-green-100 text-green-800',
  analyst: 'bg-orange-100 text-orange-800',
  viewer: 'bg-gray-100 text-gray-800',
};

export const STATUS_COLORS = {
  active: 'bg-green-100 text-green-800',
  inactive: 'bg-gray-100 text-gray-800',
  pending: 'bg-yellow-100 text-yellow-800',
  suspended: 'bg-red-100 text-red-800',
};

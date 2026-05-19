import { User, Role, BillingPlan, Subscription, Invoice, AIProvider, PromptTemplate, QueueJob, AuditLogEntry, UsageMetric, FailedJob } from './types';

export const MOCK_USERS: User[] = [
  { id: '1', name: 'John Smith', email: 'john@company.com', role: 'admin', status: 'active', organization: 'Acme Corp', lastActive: '2026-05-18T14:30:00Z', createdAt: '2025-01-15T08:00:00Z', permissions: ['all'] },
  { id: '2', name: 'Sarah Johnson', email: 'sarah@company.com', role: 'manager', status: 'active', organization: 'Acme Corp', lastActive: '2026-05-18T13:00:00Z', createdAt: '2025-03-20T10:00:00Z', permissions: ['read', 'update'] },
  { id: '3', name: 'Mike Chen', email: 'mike@company.com', role: 'analyst', status: 'active', organization: 'Acme Corp', lastActive: '2026-05-18T12:00:00Z', createdAt: '2025-06-10T14:00:00Z', permissions: ['read'] },
  { id: '4', name: 'Emily Davis', email: 'emily@company.com', role: 'viewer', status: 'inactive', organization: 'Tech Inc', lastActive: '2026-04-15T09:00:00Z', createdAt: '2025-08-05T11:00:00Z', permissions: ['read'] },
  { id: '5', name: 'David Wilson', email: 'david@company.com', role: 'super_admin', status: 'active', organization: 'System', lastActive: '2026-05-18T15:00:00Z', createdAt: '2024-01-01T00:00:00Z', permissions: ['all'] },
];

export const MOCK_ROLES: Role[] = [
  { id: 'super_admin', name: 'Super Admin', description: 'Full system access', permissions: ['all'], userCount: 1 },
  { id: 'admin', name: 'Admin', description: 'Administrative access', permissions: ['users', 'billing', 'settings', 'analytics'], userCount: 2 },
  { id: 'manager', name: 'Manager', description: 'Team management', permissions: ['team', 'documents', 'reports'], userCount: 5 },
  { id: 'analyst', name: 'Analyst', description: 'Analysis access', permissions: ['documents', 'analysis'], userCount: 12 },
  { id: 'viewer', name: 'Viewer', description: 'Read only access', permissions: ['read'], userCount: 8 },
];

export const MOCK_BILLING_PLANS: BillingPlan[] = [
  { id: 'starter', name: 'Starter', price: 29, interval: 'monthly', features: ['5 Users', '100 Documents/mo', 'Basic Analytics'], limits: { users: 5, documents: 100, apiCalls: 1000, storage: 1 } },
  { id: 'professional', name: 'Professional', price: 99, interval: 'monthly', features: ['20 Users', '500 Documents/mo', 'Advanced Analytics', 'Priority Support'], limits: { users: 20, documents: 500, apiCalls: 10000, storage: 10 } },
  { id: 'enterprise', name: 'Enterprise', price: 299, interval: 'monthly', features: ['Unlimited Users', 'Unlimited Documents', 'Custom Analytics', '24/7 Support', 'SSO'], limits: { users: -1, documents: -1, apiCalls: -1, storage: 100 } },
];

export const MOCK_SUBSCRIPTIONS: Subscription[] = [
  { id: 'sub-1', userId: '1', planId: 'enterprise', status: 'active', currentPeriodStart: '2026-05-01', currentPeriodEnd: '2026-06-01', cancelAtPeriodEnd: false },
];

export const MOCK_INVOICES: Invoice[] = [
  { id: 'inv-1', userId: '1', amount: 299, currency: 'USD', status: 'paid', createdAt: '2026-05-01', paidAt: '2026-05-01', description: 'Enterprise Plan - May 2026' },
  { id: 'inv-2', userId: '1', amount: 299, currency: 'USD', status: 'paid', createdAt: '2026-04-01', paidAt: '2026-04-01', description: 'Enterprise Plan - April 2026' },
  { id: 'inv-3', userId: '1', amount: 299, currency: 'USD', status: 'pending', createdAt: '2026-03-01', description: 'Enterprise Plan - March 2026' },
];

export const MOCK_AI_PROVIDERS: AIProvider[] = [
  { id: 'openai', name: 'OpenAI', type: 'openai', apiKeyMasked: 'sk-****-xxxx', isActive: true, models: [{ id: 'gpt-4', name: 'GPT-4', provider: 'OpenAI', maxTokens: 8192, costPer1kTokens: 0.03, isDefault: true }], settings: { temperature: 0.7, maxTokens: 2048, topP: 1, frequencyPenalty: 0, presencePenalty: 0 } },
  { id: 'anthropic', name: 'Anthropic', type: 'anthropic', apiKeyMasked: 'sk-****-xxxx', isActive: true, models: [{ id: 'claude-3', name: 'Claude 3', provider: 'Anthropic', maxTokens: 16384, costPer1kTokens: 0.015, isDefault: false }], settings: { temperature: 0.7, maxTokens: 4096, topP: 1, frequencyPenalty: 0, presencePenalty: 0 } },
];

export const MOCK_PROMPTS: PromptTemplate[] = [
  { id: '1', name: 'Document Extraction', description: 'Extract key information from tender documents', category: 'extraction', content: 'Extract {fields} from the document...', variables: [{ name: 'fields', type: 'string', required: true }], version: 2, isActive: true, createdAt: '2025-01-15', updatedAt: '2026-03-10', createdBy: 'Admin' },
  { id: '2', name: 'Risk Analysis', description: 'Analyze and identify risks in documents', category: 'risk', content: 'Analyze risks: {riskCategories}...', variables: [{ name: 'riskCategories', type: 'select', required: true, options: ['financial', 'technical', 'legal'] }], version: 1, isActive: true, createdAt: '2025-06-20', updatedAt: '2025-06-20', createdBy: 'Admin' },
  { id: '3', name: 'Summary Generation', description: 'Generate executive summary', category: 'summary', content: 'Create a summary focusing on: {focusAreas}...', variables: [{ name: 'focusAreas', type: 'string', required: false, defaultValue: 'key points' }], version: 1, isActive: false, createdAt: '2025-09-01', updatedAt: '2025-09-01', createdBy: 'Admin' },
];

export const MOCK_QUEUE_JOBS: QueueJob[] = [
  { id: 'job-1', name: 'Document Processing', status: 'processing', progress: 75, priority: 'high', queue: 'documents', worker: 'worker-1', attempts: 1, maxAttempts: 3, createdAt: '2026-05-18T14:00:00Z', startedAt: '2026-05-18T14:01:00Z', payload: { documentId: 'doc-123' } },
  { id: 'job-2', name: 'Email Notification', status: 'pending', progress: 0, priority: 'normal', queue: 'notifications', attempts: 0, maxAttempts: 5, createdAt: '2026-05-18T14:30:00Z', payload: { userId: 'user-1', type: 'reminder' } },
  { id: 'job-3', name: 'Report Generation', status: 'completed', progress: 100, priority: 'low', queue: 'reports', worker: 'worker-2', attempts: 1, maxAttempts: 3, createdAt: '2026-05-18T10:00:00Z', startedAt: '2026-05-18T10:01:00Z', completedAt: '2026-05-18T10:15:00Z', result: { reportId: 'rep-456' } },
  { id: 'job-4', name: 'AI Analysis', status: 'failed', progress: 45, priority: 'urgent', queue: 'ai', attempts: 3, maxAttempts: 3, createdAt: '2026-05-18T08:00:00Z', startedAt: '2026-05-18T08:01:00Z', failedAt: '2026-05-18T08:05:00Z', error: 'AI provider timeout', payload: { analysisType: 'risk' } },
  { id: 'job-5', name: 'Data Export', status: 'retry', progress: 30, priority: 'normal', queue: 'exports', attempts: 2, maxAttempts: 5, createdAt: '2026-05-18T12:00:00Z', startedAt: '2026-05-18T12:01:00Z', error: 'Connection timeout', payload: { format: 'csv' } },
];

export const MOCK_AUDIT_LOGS: AuditLogEntry[] = [
  { id: 'audit-1', userId: '1', userName: 'John Smith', userRole: 'admin', action: 'FILE_UPLOADED', resource: 'document', resourceId: 'doc-123', details: 'Uploaded tender_document.pdf (2.5 MB)', ipAddress: '192.168.1.100', userAgent: 'Chrome/120', timestamp: '2026-05-19T10:30:00Z', actionType: 'upload' },
  { id: 'audit-2', userId: '5', userName: 'David Wilson', userRole: 'super_admin', action: 'SETTINGS_UPDATED', resource: 'settings', details: 'Updated AI provider configuration', ipAddress: '192.168.1.5', userAgent: 'Firefox/121', timestamp: '2026-05-19T09:00:00Z', actionType: 'admin_action' },
  { id: 'audit-3', userId: '2', userName: 'Sarah Johnson', userRole: 'manager', action: 'TENDER_EXPORTED', resource: 'tender', resourceId: 'tend-456', details: 'Exported IT Infrastructure Tender as PDF', ipAddress: '192.168.1.101', userAgent: 'Chrome/120', timestamp: '2026-05-19T08:30:00Z', actionType: 'export' },
  { id: 'audit-4', userId: '1', userName: 'John Smith', userRole: 'admin', action: 'AI_ANALYSIS_COMPLETED', resource: 'analysis', resourceId: 'analysis-789', details: 'AI analysis completed for Tender #456 - 85% confidence', ipAddress: '192.168.1.100', userAgent: 'Chrome/120', timestamp: '2026-05-19T08:00:00Z', actionType: 'ai_generation' },
  { id: 'audit-5', userId: '5', userName: 'David Wilson', userRole: 'super_admin', action: 'SUBSCRIPTION_UPGRADED', resource: 'billing', details: 'Upgraded to Enterprise plan ($299/mo)', ipAddress: '192.168.1.5', userAgent: 'Safari/17', timestamp: '2026-05-18T15:00:00Z', actionType: 'billing' },
  { id: 'audit-6', userId: '2', userName: 'Sarah Johnson', userRole: 'manager', action: 'DOCUMENT_DELETED', resource: 'document', resourceId: 'doc-999', details: 'Deleted old_tender.pdf', ipAddress: '192.168.1.101', userAgent: 'Chrome/120', timestamp: '2026-05-18T14:00:00Z', actionType: 'delete' },
  { id: 'audit-7', userId: '1', userName: 'John Smith', userRole: 'admin', action: 'USER_CREATED', resource: 'users', resourceId: 'user-5', details: 'Created new user: emily@example.com', ipAddress: '192.168.1.1', userAgent: 'Chrome/120', timestamp: '2026-05-18T13:30:00Z', actionType: 'user' },
  { id: 'audit-8', userId: '5', userName: 'David Wilson', userRole: 'super_admin', action: 'USER_ROLE_CHANGED', resource: 'users', resourceId: 'user-3', details: 'Changed user role from viewer to analyst', ipAddress: '192.168.1.5', userAgent: 'Firefox/121', timestamp: '2026-05-18T12:00:00Z', actionType: 'admin_action' },
];

export const MOCK_USAGE_METRICS: UsageMetric[] = [
  { date: '2026-05-12', apiCalls: 1200, documentsProcessed: 45, tokensUsed: 45000, cost: 12.50 },
  { date: '2026-05-13', apiCalls: 1500, documentsProcessed: 52, tokensUsed: 52000, cost: 15.20 },
  { date: '2026-05-14', apiCalls: 1100, documentsProcessed: 38, tokensUsed: 40000, cost: 11.00 },
  { date: '2026-05-15', apiCalls: 1800, documentsProcessed: 65, tokensUsed: 60000, cost: 18.50 },
  { date: '2026-05-16', apiCalls: 2000, documentsProcessed: 72, tokensUsed: 70000, cost: 22.00 },
  { date: '2026-05-17', apiCalls: 1900, documentsProcessed: 68, tokensUsed: 65000, cost: 19.50 },
  { date: '2026-05-18', apiCalls: 2100, documentsProcessed: 75, tokensUsed: 75000, cost: 24.00 },
];

export const MOCK_FAILED_JOBS: FailedJob[] = [
  { id: 'fail-1', jobName: 'AI Analysis', queue: 'ai', failedAt: '2026-05-18T08:05:00Z', error: 'AI provider timeout: Request exceeded 30s', attemptCount: 3, lastAttemptAt: '2026-05-18T08:05:00Z', retryable: true, payload: { analysisType: 'risk', documentId: 'doc-789' } },
  { id: 'fail-2', jobName: 'Data Export', queue: 'exports', failedAt: '2026-05-17T16:30:00Z', error: 'Connection refused: External service unavailable', attemptCount: 5, lastAttemptAt: '2026-05-17T16:30:00Z', retryable: false, payload: { format: 'xlsx', userId: 'user-2' } },
  { id: 'fail-3', jobName: 'Email Notification', queue: 'notifications', failedAt: '2026-05-16T10:15:00Z', error: 'Invalid email address', attemptCount: 2, lastAttemptAt: '2026-05-16T10:15:00Z', retryable: true, payload: { userId: 'user-99', type: 'alert' } },
];

export const ANALYTICS_CARDS = [
  { title: 'Total Users', value: '28', change: 12, changeType: 'increase' as const, trend: 'up' as const },
  { title: 'Active Documents', value: '1,247', change: 8, changeType: 'increase' as const, trend: 'up' as const },
  { title: 'API Calls Today', value: '2,100', change: 15, changeType: 'increase' as const, trend: 'up' as const },
  { title: 'Monthly Cost', value: '$2,847', change: 5, changeType: 'decrease' as const, trend: 'down' as const },
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
] as const;

export const ROLE_COLORS = {
  super_admin: 'bg-purple-100 text-purple-800',
  admin: 'bg-blue-100 text-blue-800',
  manager: 'bg-green-100 text-green-800',
  analyst: 'bg-yellow-100 text-yellow-800',
  viewer: 'bg-gray-100 text-gray-800',
};

export const STATUS_COLORS = {
  active: 'bg-green-100 text-green-800',
  inactive: 'bg-gray-100 text-gray-800',
  suspended: 'bg-red-100 text-red-800',
  pending: 'bg-yellow-100 text-yellow-800',
  paid: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  pending_payment: 'bg-yellow-100 text-yellow-800',
};

export const JOB_STATUS_COLORS = {
  pending: 'bg-gray-100 text-gray-800',
  processing: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  retry: 'bg-yellow-100 text-yellow-800',
};

export const PRIORITY_COLORS = {
  low: 'bg-gray-100 text-gray-800',
  normal: 'bg-blue-100 text-blue-800',
  high: 'bg-orange-100 text-orange-800',
  urgent: 'bg-red-100 text-red-800',
};

export const AUDIT_ACTION_TYPE_COLORS: Record<string, string> = {
  upload: 'bg-blue-100 text-blue-800',
  delete: 'bg-red-100 text-red-800',
  export: 'bg-green-100 text-green-800',
  admin_action: 'bg-purple-100 text-purple-800',
  ai_generation: 'bg-cyan-100 text-cyan-800',
  billing: 'bg-yellow-100 text-yellow-800',
  user: 'bg-indigo-100 text-indigo-800',
  document: 'bg-orange-100 text-orange-800',
  tender: 'bg-teal-100 text-teal-800',
  bid: 'bg-pink-100 text-pink-800',
  settings: 'bg-gray-100 text-gray-800',
  auth: 'bg-amber-100 text-amber-800',
};
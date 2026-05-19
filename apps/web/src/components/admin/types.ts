export type UserRole = 'super_admin' | 'admin' | 'manager' | 'analyst' | 'viewer';
export type UserStatus = 'active' | 'inactive' | 'suspended' | 'pending';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  avatar?: string;
  organization: string;
  lastActive: string;
  createdAt: string;
  permissions: string[];
}

export interface Permission {
  id: string;
  name: string;
  description: string;
  resource: string;
  action: 'create' | 'read' | 'update' | 'delete' | 'admin';
}

export interface Role {
  id: UserRole;
  name: string;
  description: string;
  permissions: string[];
  userCount: number;
}

export interface BillingPlan {
  id: string;
  name: string;
  price: number;
  interval: 'monthly' | 'annual';
  features: string[];
  limits: {
    users: number;
    documents: number;
    apiCalls: number;
    storage: number;
  };
  stripePriceId?: string;
}

export interface Subscription {
  id: string;
  userId: string;
  planId: string;
  status: 'active' | 'canceled' | 'past_due' | 'trialing';
  currentPeriodStart: string;
  currentPeriodEnd: string;
  cancelAtPeriodEnd: boolean;
}

export interface Invoice {
  id: string;
  userId: string;
  amount: number;
  currency: string;
  status: 'paid' | 'pending' | 'failed' | 'refunded';
  createdAt: string;
  paidAt?: string;
  description: string;
}

export interface PaymentMethod {
  id: string;
  type: 'card' | 'bank';
  last4: string;
  brand?: string;
  expiryMonth?: number;
  expiryYear?: number;
  isDefault: boolean;
}

export interface AIProvider {
  id: string;
  name: string;
  type: 'openai' | 'anthropic' | 'azure' | 'custom';
  apiKeyMasked: string;
  endpoint?: string;
  isActive: boolean;
  models: AIModel[];
  settings: AIProviderSettings;
}

export interface AIModel {
  id: string;
  name: string;
  provider: string;
  maxTokens: number;
  costPer1kTokens: number;
  isDefault: boolean;
}

export interface AIProviderSettings {
  temperature: number;
  maxTokens: number;
  topP: number;
  frequencyPenalty: number;
  presencePenalty: number;
}

export interface PromptTemplate {
  id: string;
  name: string;
  description: string;
  category: 'extraction' | 'analysis' | 'summary' | 'risk' | 'custom';
  content: string;
  variables: PromptVariable[];
  version: number;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
}

export interface PromptVariable {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'select';
  required: boolean;
  defaultValue?: string;
  options?: string[];
}

export interface QueueJob {
  id: string;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'retry';
  progress: number;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  queue: string;
  worker?: string;
  attempts: number;
  maxAttempts: number;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  failedAt?: string;
  error?: string;
  payload: Record<string, unknown>;
  result?: Record<string, unknown>;
}

export interface AuditLogEntry {
  id: string;
  userId: string;
  userName: string;
  userRole: UserRole;
  action: string;
  actionType?: 'upload' | 'delete' | 'export' | 'admin_action' | 'ai_generation' | 'billing' | 'user' | 'document' | 'tender' | 'bid' | 'settings' | 'auth';
  resource: string;
  resourceId?: string;
  details: string;
  ipAddress: string;
  userAgent: string;
  timestamp: string;
  previousState?: Record<string, unknown>;
  newState?: Record<string, unknown>;
}

export interface UsageMetric {
  date: string;
  apiCalls: number;
  documentsProcessed: number;
  tokensUsed: number;
  cost: number;
}

export interface AnalyticsCard {
  title: string;
  value: string | number;
  change: number;
  changeType: 'increase' | 'decrease' | 'neutral';
  trend: 'up' | 'down' | 'stable';
  sparklineData?: number[];
}

export interface FailedJob {
  id: string;
  jobName: string;
  queue: string;
  failedAt: string;
  error: string;
  attemptCount: number;
  lastAttemptAt: string;
  retryable: boolean;
  payload: Record<string, unknown>;
}

export interface FilterOption {
  value: string;
  label: string;
}

export interface AdvancedFilter {
  field: string;
  operator: 'eq' | 'ne' | 'gt' | 'lt' | 'gte' | 'lte' | 'contains' | 'in';
  value: string | string[] | number | boolean;
}

export type AdminModule = 
  | 'users' 
  | 'billing' 
  | 'ai_settings' 
  | 'prompts' 
  | 'queue' 
  | 'audit' 
  | 'analytics' 
  | 'failed_jobs';

export interface PaginationState {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}

export interface SortState {
  field: string;
  direction: 'asc' | 'desc';
}
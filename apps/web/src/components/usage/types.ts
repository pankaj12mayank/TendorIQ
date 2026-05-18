export type FeatureKey = 
  | 'uploads'
  | 'storage'
  | 'ai_tokens'
  | 'proposal_generations'
  | 'exports'
  | 'api_requests'
  | 'documents'
  | 'users'
  | 'tenders'
  | 'bids'
  | 'ai_analysis'
  | 'ocr_pages';

export type ActionType = 
  | 'upload'
  | 'download'
  | 'api_call'
  | 'generate'
  | 'analyze'
  | 'ocr_process'
  | 'export';

export type AlertType = 'warning' | 'critical' | 'exceeded';
export type AlertStatus = 'active' | 'read' | 'dismissed';
export type ResetPeriod = 'daily' | 'weekly' | 'monthly' | 'yearly' | 'never';

export interface UsageRecord {
  id: string;
  userId: string;
  subscriptionId?: string;
  featureKey: FeatureKey;
  actionType: ActionType;
  quantity: number;
  unit?: string;
  metadata?: Record<string, unknown>;
  ipAddress?: string;
  userAgent?: string;
  createdAt: string;
}

export interface DailyUsageSummary {
  id: string;
  userId: string;
  subscriptionId?: string;
  featureKey: FeatureKey;
  date: string;
  totalCount: number;
  totalCost: number;
  createdAt: string;
  updatedAt: string;
}

export interface MonthlyUsageSummary {
  id: string;
  userId: string;
  subscriptionId?: string;
  featureKey: FeatureKey;
  year: number;
  month: number;
  totalCount: number;
  totalCost: number;
  createdAt: string;
}

export interface QuotaAlert {
  id: string;
  userId: string;
  subscriptionId?: string;
  featureKey: FeatureKey;
  alertType: AlertType;
  thresholdPercent: number;
  currentPercent: number;
  isRead: boolean;
  isDismissed: boolean;
  createdAt: string;
  readAt?: string;
}

export interface AdminQuotaOverride {
  id: string;
  userId: string;
  subscriptionId?: string;
  featureKey: FeatureKey;
  originalLimit?: number;
  newLimit: number;
  reason: string;
  grantedBy: string;
  grantedByName?: string;
  expiresAt?: string;
  isActive: boolean;
  createdAt: string;
  revokedAt?: string;
}

export interface Quota {
  id: string;
  userId: string;
  subscriptionId?: string;
  featureKey: FeatureKey;
  limitValue: number | null;
  usedValue: number;
  resetPeriod: ResetPeriod;
  lastResetAt?: string;
  nextResetAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface QuotaStatus {
  featureKey: FeatureKey;
  featureName: string;
  limit: number | null;
  used: number;
  remaining: number | null;
  percentage: number;
  isUnlimited: boolean;
  isExceeded: boolean;
  resetPeriod: ResetPeriod;
  nextResetAt?: string;
  alertLevel?: AlertType;
}

export interface UsageSummary {
  totalUsage: number;
  totalCost: number;
  periodStart: string;
  periodEnd: string;
  breakdown: FeatureBreakdown[];
}

export interface FeatureBreakdown {
  featureKey: FeatureKey;
  featureName: string;
  count: number;
  cost: number;
  percentage: number;
}

export interface QuotaCheckResult {
  allowed: boolean;
  currentUsage: number;
  limit: number | null;
  remaining: number | null;
  percentage: number;
  required: number;
  exceeded: boolean;
  upgradeRequired: boolean;
  suggestedPlan?: 'pro' | 'enterprise';
}

export interface AlertThreshold {
  featureKey: FeatureKey;
  warningPercent: number;
  criticalPercent: number;
  exceededPercent: number;
}

export interface UsageTrend {
  date: string;
  usage: number;
  cost: number;
}

export interface RealTimeUsageUpdate {
  featureKey: FeatureKey;
  change: number;
  newTotal: number;
  timestamp: string;
}

export interface OverrideRequest {
  userId: string;
  featureKey: FeatureKey;
  newLimit: number;
  reason: string;
  duration?: string;
}

export interface OverrideResponse {
  success: boolean;
  override?: AdminQuotaOverride;
  error?: string;
}
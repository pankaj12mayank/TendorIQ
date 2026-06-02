export type BillingInterval = 'monthly';

export interface PlanFeature {
  key: string;
  name: string;
  limit: number | null;
  unit: string;
  isEnabled: boolean;
}

export interface Plan {
  id: string;
  name: string;
  displayName: string;
  description: string;
  priceMonthly: number;
  priceMonthlyUsd: number;
  currency: string;
  isDemo: boolean;
  trialDays: number;
  isActive: boolean;
  expiryPeriodDays: number;
  features: PlanFeature[];
  apiPlanId: string;
}

export interface SubscriptionPlan {
  id: string;
  name: string;
  displayName: string;
  description: string;
  priceMonthly: number;
  priceAnnual: number;
  currency: string;
  trialDays: number;
  isActive: boolean;
  features: string[];
}

export interface Subscription {
  id: string;
  userId: string;
  planId: string;
  plan: SubscriptionPlan;
  status: string;
  billingInterval: string;
  currentPeriodStart: string;
  currentPeriodEnd: string;
  cancelAtPeriodEnd: boolean;
  createdAt: string;
  updatedAt: string;
  limits: Record<string, { current: number; max: number }> | null;
  canUseSystem: boolean;
  isExpired: boolean;
  upgradeRequired: boolean;
}

export interface Invoice {
  id: string;
  payment_date: string | null;
  amount: number;
  currency: string;
  status: string;
  provider: string;
  invoice: string;
  plan?: string | null;
  expiry?: string | null;
}

export interface PaymentMethod {
  id: string;
  brand?: string;
  last4?: string;
  is_default?: boolean;
}

export interface UsageEntry {
  operation: string;
  featureKey: string;
  used: number;
  limit: number | null;
  remaining: number | null;
  isExceeded: boolean;
}

export interface QuotaStatus {
  featureKey: string;
  featureName: string;
  limit: number | null;
  used: number;
  remaining: number | null;
  percentage: number;
  isUnlimited: boolean;
  isExceeded: boolean;
  resetPeriod: string;
  alertLevel: string | null;
}

export interface PlanChangeResult {
  success: boolean;
  plan?: string;
  message?: string;
  subscription?: Subscription;
  error?: string;
}

export interface PaymentHistoryItem {
  id: string;
  payment_date: string | null;
  amount: number;
  currency: string;
  status: string;
  provider: string;
  invoice: string;
  plan?: string | null;
  expiry?: string | null;
}

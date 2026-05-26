export type BillingInterval = 'monthly' | 'yearly';

export interface Plan {
  id: string;
  name: string;
  price: number;
  currency?: string;
  interval?: BillingInterval;
  features?: string[];
}

export interface Subscription {
  id: string;
  plan: string;
  status: string;
  current_period_end?: string;
}

export interface Invoice {
  id: string;
  amount: number;
  status: string;
  created_at?: string;
}

export interface PaymentMethod {
  id: string;
  brand?: string;
  last4?: string;
  is_default?: boolean;
}

export interface QuotaStatus {
  resource: string;
  used: number;
  limit: number;
}

export interface PlanChangeResult {
  subscription: Subscription;
}

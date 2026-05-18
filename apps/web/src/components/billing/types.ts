export type PlanName = 'free' | 'pro' | 'enterprise';

export type BillingInterval = 'monthly' | 'annual';

export type SubscriptionStatus = 
  | 'trialing' 
  | 'active' 
  | 'past_due' 
  | 'canceled' 
  | 'unpaid' 
  | 'paused';

export type InvoiceStatus = 'draft' | 'pending' | 'paid' | 'failed' | 'refunded' | 'void';

export type PaymentStatus = 'processing' | 'succeeded' | 'failed' | 'canceled';

export type PaymentMethodType = 'card' | 'bank_account' | 'paypal';

export type PlanChangeType = 'upgrade' | 'downgrade' | 'cancel' | 'reactivate' | 'trial_end';

export interface PlanFeature {
  key: string;
  name: string;
  limit: number | null;
  unit: string;
  isEnabled: boolean;
}

export interface Plan {
  id: string;
  name: PlanName;
  displayName: string;
  description: string;
  priceMonthly: number;
  priceAnnual: number;
  currency: string;
  trialDays: number;
  isActive: boolean;
  features: PlanFeature[];
  stripePriceIdMonthly?: string;
  stripePriceIdAnnual?: string;
}

export interface Subscription {
  id: string;
  userId: string;
  planId: string;
  plan?: Plan;
  status: SubscriptionStatus;
  billingInterval: BillingInterval;
  stripeSubscriptionId?: string;
  stripeCustomerId?: string;
  currentPeriodStart: string;
  currentPeriodEnd: string;
  trialEnd?: string;
  cancelAtPeriodEnd: boolean;
  canceledAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Invoice {
  id: string;
  subscriptionId: string;
  userId: string;
  stripeInvoiceId?: string;
  invoiceNumber: string;
  amount: number;
  currency: string;
  status: InvoiceStatus;
  description: string;
  paidAt?: string;
  dueDate: string;
  billingPeriodStart: string;
  billingPeriodEnd: string;
  items?: InvoiceItem[];
  createdAt: string;
}

export interface InvoiceItem {
  description: string;
  amount: number;
  quantity: number;
}

export interface Payment {
  id: string;
  userId: string;
  subscriptionId?: string;
  invoiceId?: string;
  stripePaymentIntentId?: string;
  amount: number;
  currency: string;
  status: PaymentStatus;
  paymentMethod: PaymentMethodType;
  paymentMethodDetails?: PaymentMethodDetails;
  failureCode?: string;
  failureMessage?: string;
  createdAt: string;
}

export interface PaymentMethodDetails {
  brand?: string;
  last4?: string;
  expiryMonth?: number;
  expiryYear?: number;
  bankName?: string;
}

export interface PaymentMethod {
  id: string;
  userId: string;
  stripePaymentMethodId: string;
  type: PaymentMethodType;
  brand?: string;
  last4?: string;
  expiryMonth?: number;
  expiryYear?: number;
  bankName?: string;
  isDefault: boolean;
  isActive: boolean;
  createdAt: string;
}

export interface UsageRecord {
  id: string;
  userId: string;
  subscriptionId?: string;
  featureKey: string;
  count: number;
  periodStart: string;
  periodEnd: string;
}

export interface QuotaStatus {
  featureKey: string;
  featureName: string;
  used: number;
  limit: number | null;
  remaining: number | null;
  isUnlimited: boolean;
  resetDate?: string;
}

export interface PlanChangeRequest {
  fromPlanId: string;
  toPlanId: string;
  changeType: PlanChangeType;
  billingInterval?: BillingInterval;
  effectiveDate?: string;
  reason?: string;
}

export interface PlanChangeResult {
  success: boolean;
  prorationAmount?: number;
  immediateCharge?: boolean;
  nextBillingDate?: string;
  error?: string;
}

export interface SubscriptionLimits {
  users: number | null;
  documents: number | null;
  apiCalls: number | null;
  storage: number | null;
  tenders: number | null;
  bids: number | null;
}

export interface UpgradeDowngradeOption {
  plan: Plan;
  price: number;
  billingInterval: BillingInterval;
  savings?: number;
  isRecommended?: boolean;
}

export interface BillingPortalResult {
  url: string;
  expiresAt: string;
}

export interface QuotaExceededError {
  featureKey: string;
  featureName: string;
  used: number;
  limit: number;
  required: number;
  upgradePlan?: PlanName;
}
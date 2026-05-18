import { Plan, Subscription, Invoice, Payment, QuotaStatus, UsageRecord } from './types';

export const PLANS: Plan[] = [
  {
    id: 'plan_free',
    name: 'free',
    displayName: 'Free',
    description: 'Perfect for getting started with basic tender management.',
    priceMonthly: 0,
    priceAnnual: 0,
    currency: 'USD',
    trialDays: 0,
    isActive: true,
    features: [
      { key: 'users', name: 'Team Members', limit: 2, unit: 'users', isEnabled: true },
      { key: 'documents', name: 'Documents', limit: 50, unit: 'documents', isEnabled: true },
      { key: 'api_calls', name: 'API Calls', limit: 500, unit: 'calls', isEnabled: true },
      { key: 'storage', name: 'Storage', limit: 1, unit: 'GB', isEnabled: true },
      { key: 'tenders', name: 'Tenders', limit: 10, unit: 'tenders', isEnabled: true },
      { key: 'bids', name: 'Bids', limit: 25, unit: 'bids', isEnabled: true },
      { key: 'ai_analysis', name: 'AI Analysis', limit: 25, unit: 'analyses', isEnabled: true },
      { key: 'document_ocr', name: 'Document OCR', limit: 10, unit: 'pages', isEnabled: true },
      { key: 'templates', name: 'Templates', limit: 5, unit: 'templates', isEnabled: true },
      { key: 'analytics', name: 'Analytics', limit: null, unit: '', isEnabled: true },
      { key: 'support', name: 'Support', limit: null, unit: 'community', isEnabled: true },
      { key: 'integrations', name: 'Integrations', limit: 0, unit: 'integrations', isEnabled: true },
      { key: 'api_access', name: 'API Access', limit: null, unit: '', isEnabled: false },
      { key: 'sso', name: 'SSO', limit: null, unit: '', isEnabled: false },
      { key: 'custom_branding', name: 'Custom Branding', limit: null, unit: '', isEnabled: false },
      { key: 'priority_support', name: 'Priority Support', limit: null, unit: '', isEnabled: false },
    ],
  },
  {
    id: 'plan_pro',
    name: 'pro',
    displayName: 'Professional',
    description: 'Ideal for growing teams that need more power and flexibility.',
    priceMonthly: 4900,
    priceAnnual: 4700,
    currency: 'USD',
    trialDays: 14,
    isActive: true,
    features: [
      { key: 'users', name: 'Team Members', limit: 10, unit: 'users', isEnabled: true },
      { key: 'documents', name: 'Documents', limit: 500, unit: 'documents', isEnabled: true },
      { key: 'api_calls', name: 'API Calls', limit: 5000, unit: 'calls', isEnabled: true },
      { key: 'storage', name: 'Storage', limit: 20, unit: 'GB', isEnabled: true },
      { key: 'tenders', name: 'Tenders', limit: 100, unit: 'tenders', isEnabled: true },
      { key: 'bids', name: 'Bids', limit: 250, unit: 'bids', isEnabled: true },
      { key: 'ai_analysis', name: 'AI Analysis', limit: 200, unit: 'analyses', isEnabled: true },
      { key: 'document_ocr', name: 'Document OCR', limit: 100, unit: 'pages', isEnabled: true },
      { key: 'templates', name: 'Templates', limit: 50, unit: 'templates', isEnabled: true },
      { key: 'analytics', name: 'Analytics', limit: null, unit: '', isEnabled: true },
      { key: 'support', name: 'Support', limit: null, unit: 'email', isEnabled: true },
      { key: 'integrations', name: 'Integrations', limit: 5, unit: 'integrations', isEnabled: true },
      { key: 'api_access', name: 'API Access', limit: null, unit: '', isEnabled: true },
      { key: 'sso', name: 'SSO', limit: null, unit: '', isEnabled: false },
      { key: 'custom_branding', name: 'Custom Branding', limit: null, unit: '', isEnabled: false },
      { key: 'priority_support', name: 'Priority Support', limit: null, unit: '', isEnabled: false },
    ],
  },
  {
    id: 'plan_enterprise',
    name: 'enterprise',
    displayName: 'Enterprise',
    description: 'For organizations that require advanced features and dedicated support.',
    priceMonthly: 19900,
    priceAnnual: 17900,
    currency: 'USD',
    trialDays: 30,
    isActive: true,
    features: [
      { key: 'users', name: 'Team Members', limit: null, unit: 'unlimited', isEnabled: true },
      { key: 'documents', name: 'Documents', limit: null, unit: 'unlimited', isEnabled: true },
      { key: 'api_calls', name: 'API Calls', limit: null, unit: 'unlimited', isEnabled: true },
      { key: 'storage', name: 'Storage', limit: 500, unit: 'GB', isEnabled: true },
      { key: 'tenders', name: 'Tenders', limit: null, unit: 'unlimited', isEnabled: true },
      { key: 'bids', name: 'Bids', limit: null, unit: 'unlimited', isEnabled: true },
      { key: 'ai_analysis', name: 'AI Analysis', limit: null, unit: 'unlimited', isEnabled: true },
      { key: 'document_ocr', name: 'Document OCR', limit: null, unit: 'unlimited', isEnabled: true },
      { key: 'templates', name: 'Templates', limit: null, unit: 'unlimited', isEnabled: true },
      { key: 'analytics', name: 'Analytics', limit: null, unit: '', isEnabled: true },
      { key: 'support', name: 'Support', limit: null, unit: 'dedicated', isEnabled: true },
      { key: 'integrations', name: 'Integrations', limit: null, unit: 'unlimited', isEnabled: true },
      { key: 'api_access', name: 'API Access', limit: null, unit: '', isEnabled: true },
      { key: 'sso', name: 'SSO', limit: null, unit: '', isEnabled: true },
      { key: 'custom_branding', name: 'Custom Branding', limit: null, unit: '', isEnabled: true },
      { key: 'priority_support', name: 'Priority Support', limit: null, unit: '', isEnabled: true },
    ],
  },
];

export const MOCK_SUBSCRIPTION: Subscription = {
  id: 'sub_1a2b3c4d5e6f',
  userId: 'user_123',
  planId: 'plan_pro',
  plan: PLANS.find(p => p.id === 'plan_pro'),
  status: 'active',
  billingInterval: 'monthly',
  stripeSubscriptionId: 'sub_stripe_123',
  stripeCustomerId: 'cus_stripe_456',
  currentPeriodStart: '2026-05-01T00:00:00Z',
  currentPeriodEnd: '2026-06-01T00:00:00Z',
  createdAt: '2026-01-15T10:30:00Z',
  updatedAt: '2026-05-01T00:00:00Z',
};

export const MOCK_INVOICES: Invoice[] = [
  {
    id: 'inv_1',
    subscriptionId: 'sub_1a2b3c4d5e6f',
    userId: 'user_123',
    invoiceNumber: 'INV-2026-0005',
    amount: 4900,
    currency: 'USD',
    status: 'paid',
    description: 'Professional Plan - Monthly',
    paidAt: '2026-05-01T00:00:00Z',
    dueDate: '2026-05-01T00:00:00Z',
    billingPeriodStart: '2026-05-01T00:00:00Z',
    billingPeriodEnd: '2026-06-01T00:00:00Z',
    createdAt: '2026-05-01T00:00:00Z',
  },
  {
    id: 'inv_2',
    subscriptionId: 'sub_1a2b3c4d5e6f',
    userId: 'user_123',
    invoiceNumber: 'INV-2026-0004',
    amount: 4900,
    currency: 'USD',
    status: 'paid',
    description: 'Professional Plan - Monthly',
    paidAt: '2026-04-01T00:00:00Z',
    dueDate: '2026-04-01T00:00:00Z',
    billingPeriodStart: '2026-04-01T00:00:00Z',
    billingPeriodEnd: '2026-05-01T00:00:00Z',
    createdAt: '2026-04-01T00:00:00Z',
  },
  {
    id: 'inv_3',
    subscriptionId: 'sub_1a2b3c4d5e6f',
    userId: 'user_123',
    invoiceNumber: 'INV-2026-0003',
    amount: 4900,
    currency: 'USD',
    status: 'paid',
    description: 'Professional Plan - Monthly',
    paidAt: '2026-03-01T00:00:00Z',
    dueDate: '2026-03-01T00:00:00Z',
    billingPeriodStart: '2026-03-01T00:00:00Z',
    billingPeriodEnd: '2026-04-01T00:00:00Z',
    createdAt: '2026-03-01T00:00:00Z',
  },
  {
    id: 'inv_4',
    subscriptionId: 'sub_1a2b3c4d5e6f',
    userId: 'user_123',
    invoiceNumber: 'INV-2026-0002',
    amount: 4900,
    currency: 'USD',
    status: 'paid',
    description: 'Professional Plan - Monthly',
    paidAt: '2026-02-01T00:00:00Z',
    dueDate: '2026-02-01T00:00:00Z',
    billingPeriodStart: '2026-02-01T00:00:00Z',
    billingPeriodEnd: '2026-03-01T00:00:00Z',
    createdAt: '2026-02-01T00:00:00Z',
  },
  {
    id: 'inv_5',
    subscriptionId: 'sub_1a2b3c4d5e6f',
    userId: 'user_123',
    invoiceNumber: 'INV-2026-0001',
    amount: 4900,
    currency: 'USD',
    status: 'paid',
    description: 'Professional Plan - Monthly (Start)',
    paidAt: '2026-01-15T00:00:00Z',
    dueDate: '2026-01-15T00:00:00Z',
    billingPeriodStart: '2026-01-15T00:00:00Z',
    billingPeriodEnd: '2026-02-01T00:00:00Z',
    createdAt: '2026-01-15T00:00:00Z',
  },
];

export const MOCK_PAYMENTS = [
  { id: 'pay_1', amount: 4900, status: 'succeeded' as const, date: '2026-05-01', method: 'card', last4: '4242' },
  { id: 'pay_2', amount: 4900, status: 'succeeded' as const, date: '2026-04-01', method: 'card', last4: '4242' },
  { id: 'pay_3', amount: 4900, status: 'succeeded' as const, date: '2026-03-01', method: 'card', last4: '4242' },
  { id: 'pay_4', amount: 4900, status: 'succeeded' as const, date: '2026-02-01', method: 'card', last4: '4242' },
  { id: 'pay_5', amount: 4900, status: 'succeeded' as const, date: '2026-01-15', method: 'card', last4: '4242' },
];

export const MOCK_QUOTA_STATUS: QuotaStatus[] = [
  { featureKey: 'users', featureName: 'Team Members', used: 5, limit: 10, remaining: 5, isUnlimited: false },
  { featureKey: 'documents', featureName: 'Documents', used: 234, limit: 500, remaining: 266, isUnlimited: false },
  { featureKey: 'api_calls', featureName: 'API Calls', used: 3420, limit: 5000, remaining: 1580, isUnlimited: false },
  { featureKey: 'tenders', featureName: 'Tenders', used: 45, limit: 100, remaining: 55, isUnlimited: false },
  { featureKey: 'ai_analysis', featureName: 'AI Analysis', used: 156, limit: 200, remaining: 44, isUnlimited: false },
];

export const PLAN_COLORS = {
  free: 'bg-gray-100 text-gray-800 border-gray-200',
  pro: 'bg-blue-100 text-blue-800 border-blue-200',
  enterprise: 'bg-purple-100 text-purple-800 border-purple-200',
};

export const STATUS_COLORS = {
  trialing: 'bg-blue-100 text-blue-800',
  active: 'bg-green-100 text-green-800',
  past_due: 'bg-yellow-100 text-yellow-800',
  canceled: 'bg-red-100 text-red-800',
  unpaid: 'bg-red-100 text-red-800',
  paused: 'bg-gray-100 text-gray-800',
};

export const INVOICE_STATUS_COLORS = {
  draft: 'bg-gray-100 text-gray-800',
  pending: 'bg-yellow-100 text-yellow-800',
  paid: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  refunded: 'bg-blue-100 text-blue-800',
  void: 'bg-gray-100 text-gray-800',
};

export const FEATURE_ICONS: Record<string, string> = {
  users: 'Users',
  documents: 'FileText',
  api_calls: 'Zap',
  storage: 'HardDrive',
  tenders: 'Briefcase',
  bids: 'TrendingUp',
  ai_analysis: 'Brain',
  document_ocr: 'Scan',
  templates: 'Copy',
  analytics: 'BarChart3',
  support: 'Headphones',
  integrations: 'Puzzle',
  api_access: 'Code',
  sso: 'Shield',
  custom_branding: 'Palette',
  priority_support: 'Star',
};

export const PLAN_ORDER = ['free', 'pro', 'enterprise'] as const;

export function formatCurrency(amount: number, currency: string = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount / 100);
}

export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export function getDaysRemaining(endDate: string): number {
  const end = new Date(endDate);
  const now = new Date();
  const diff = end.getTime() - now.getTime();
  return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
}
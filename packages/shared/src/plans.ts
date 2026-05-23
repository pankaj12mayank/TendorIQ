/**
 * Billing / onboarding plan id normalization (FE aliases ↔ API slugs).
 */

export const CANONICAL_PLAN_IDS = ['free', 'starter', 'professional', 'enterprise'] as const;
export type CanonicalPlanId = (typeof CANONICAL_PLAN_IDS)[number];

const PLAN_TO_API: Record<string, CanonicalPlanId | string> = {
  plan_free: 'free',
  free: 'free',
  starter: 'starter',
  plan_starter: 'starter',
  plan_pro: 'professional',
  pro: 'professional',
  professional: 'professional',
  plan_enterprise: 'enterprise',
  enterprise: 'enterprise',
};

export function normalizePlanId(planId: string): string {
  const key = (planId || '').trim().toLowerCase();
  return PLAN_TO_API[key] ?? key;
}

export function normalizeBillingCycle(cycle: string): 'monthly' | 'yearly' {
  if (cycle === 'annual' || cycle === 'yearly') return 'yearly';
  return 'monthly';
}

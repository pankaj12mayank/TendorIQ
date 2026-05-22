/** FE plan ids used in billing UI ↔ API plan slugs (onboarding allows `free`). */

const PLAN_TO_API: Record<string, string> = {
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

export function normalizeBillingCycle(cycle: string): string {
  if (cycle === 'annual' || cycle === 'yearly') return 'yearly';
  return 'monthly';
}

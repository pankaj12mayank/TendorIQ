import { describe, expect, it, vi, beforeEach } from 'vitest';

vi.mock('@/lib/api-client', () => ({
  api: { get: vi.fn(), post: vi.fn() },
}));

import {
  mapOnboardingState,
  normalizeOnboardingStep4,
  parsePlansResponse,
  shouldCompleteOnboardingFirst,
} from '../onboarding-api';
import { CANONICAL_PLAN_IDS } from '@tendoriq/shared/plans';

describe('onboarding-api', () => {
  beforeEach(() => {
    vi.stubGlobal('localStorage', {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    });
    vi.stubGlobal('document', { cookie: '' });
  });

  it('maps API onboarding state to store patch', () => {
    const patch = mapOnboardingState({
      id: '1',
      user_id: 'u1',
      tenant_id: 't1',
      current_step: 3,
      total_steps: 5,
      step_1_completed: true,
      step_2_completed: true,
      step_3_completed: false,
      step_4_completed: false,
      step_5_completed: false,
      step_1_data: { name: 'Acme Corp' },
      step_2_data: {},
      step_3_data: {},
      step_4_data: {},
      step_5_data: {},
      is_completed: false,
    });
    expect(patch.currentStep).toBe(3);
    expect(patch.tenantName).toBe('Acme Corp');
    expect(patch.isCompleted).toBe(false);
  });

  it('normalizes plan_pro and annual for step 4 submit', () => {
    expect(normalizeOnboardingStep4({ plan_id: 'plan_pro', billing_cycle: 'annual' })).toEqual({
      plan_id: 'professional',
      billing_cycle: 'yearly',
      addons: undefined,
    });
  });

  it('fail closed when onboarding status unknown for tenant users', () => {
    expect(shouldCompleteOnboardingFirst(null, 'admin')).toBe(true);
    expect(shouldCompleteOnboardingFirst({ is_completed: false } as never, 'admin')).toBe(true);
    expect(shouldCompleteOnboardingFirst({ is_completed: true } as never, 'admin')).toBe(false);
    expect(shouldCompleteOnboardingFirst(null, 'super_admin')).toBe(false);
  });

  it('canonical plan ids cover API onboarding step 4', () => {
    expect(CANONICAL_PLAN_IDS).toContain('professional');
    expect(normalizeOnboardingStep4({ plan_id: 'plan_pro', billing_cycle: 'monthly' }).plan_id).toBe(
      'professional'
    );
  });

  it('parses plans list from API envelope', () => {
    const plans = parsePlansResponse({
      plans: [{ id: 'free', name: 'Free', description: '', price_monthly: 0, price_yearly: 0, currency: 'USD', features: [], recommended: false }],
    });
    expect(plans).toHaveLength(1);
    expect(plans[0].id).toBe('free');
  });
});

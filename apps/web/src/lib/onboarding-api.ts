import type { Plan } from '@/types/onboarding';
import { api } from '@/lib/api-client';
import { getStoredSession, setStoredSession, type AuthUser } from './auth-session';
import { normalizeBillingCycle, normalizePlanId } from './billing-plan-bridge';
import { isSuperAdmin } from '@/lib/permissions';

export interface OnboardingApiResponse {
  id: string;
  user_id: string;
  tenant_id?: string;
  current_step: number;
  total_steps: number;
  step_1_completed: boolean;
  step_2_completed: boolean;
  step_3_completed: boolean;
  step_4_completed: boolean;
  step_5_completed: boolean;
  step_1_data: Record<string, unknown>;
  step_2_data: Record<string, unknown>;
  step_3_data: Record<string, unknown>;
  step_4_data: Record<string, unknown>;
  step_5_data: Record<string, unknown>;
  is_completed: boolean;
}

export interface OnboardingSessionPayload {
  access_token: string;
  refresh_token: string;
  expires_in?: number;
}

export interface OnboardingStorePatch {
  currentStep: number;
  step1Completed: boolean;
  step2Completed: boolean;
  step3Completed: boolean;
  step4Completed: boolean;
  step5Completed: boolean;
  step1Data: Record<string, unknown>;
  step2Data: Record<string, unknown>;
  step3Data: Record<string, unknown>;
  step4Data: Record<string, unknown>;
  step5Data: Record<string, unknown>;
  isCompleted: boolean;
  tenantId: string | null;
  tenantName: string | null;
}

export function mapOnboardingState(res: OnboardingApiResponse): OnboardingStorePatch {
  const step1 = res.step_1_data ?? {};
  return {
    currentStep: res.current_step,
    step1Completed: res.step_1_completed,
    step2Completed: res.step_2_completed,
    step3Completed: res.step_3_completed,
    step4Completed: res.step_4_completed,
    step5Completed: res.step_5_completed,
    step1Data: step1,
    step2Data: res.step_2_data ?? {},
    step3Data: res.step_3_data ?? {},
    step4Data: res.step_4_data ?? {},
    step5Data: res.step_5_data ?? {},
    isCompleted: res.is_completed,
    tenantId: res.tenant_id ?? null,
    tenantName: typeof step1.name === 'string' ? step1.name : null,
  };
}

export function applyOnboardingSession(
  session: OnboardingSessionPayload | undefined,
  tenantId?: string | null
): void {
  if (!session?.access_token || typeof window === 'undefined') return;
  const stored = getStoredSession();
  const baseUser: AuthUser = stored?.user ?? {
    id: '',
    email: '',
    name: '',
  };
  setStoredSession(
    session.access_token,
    {
      ...baseUser,
      tenantId: tenantId ?? baseUser.tenantId,
      membershipRole: baseUser.membershipRole ?? 'owner',
    },
    {
      refreshToken: session.refresh_token,
      expiresInSec: session.expires_in,
    }
  );
}

export function normalizeOnboardingStep4(data: {
  plan_id: string;
  billing_cycle: string;
  addons?: string[];
}) {
  return {
    plan_id: normalizePlanId(data.plan_id),
    billing_cycle: normalizeBillingCycle(data.billing_cycle),
    addons: data.addons,
  };
}

export function parsePlansResponse(payload: { plans?: Plan[] } | Plan[]): Plan[] {
  if (Array.isArray(payload)) return payload;
  return payload.plans ?? [];
}

/** Authenticated onboarding status (shared by Clerk sign-in and password login). */
export async function fetchOnboardingStatusAuthenticated(
  accessToken: string
): Promise<OnboardingApiResponse> {
  return api.get<OnboardingApiResponse>('/api/v1/onboarding/status', {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}

/** Fail closed: unknown status or API error → send user to onboarding (except platform admin). */
export function shouldCompleteOnboardingFirst(
  status: OnboardingApiResponse | null,
  role?: string | null
): boolean {
  if (role && isSuperAdmin(role)) return false;
  if (!status) return true;
  return !status.is_completed;
}

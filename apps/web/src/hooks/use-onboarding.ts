import { useCallback, useState } from 'react';
import { api } from '@/lib/api-client';
import { useOnboardingStore } from '@/stores/onboarding-store';
import type { Plan, ExpertiseCategory } from '@/types/onboarding';
import {
  applyOnboardingSession,
  mapOnboardingState,
  normalizeOnboardingStep4,
  parsePlansResponse,
  type OnboardingSessionPayload,
} from '@/lib/onboarding-api';

export interface Step1Data {
  name: string;
  slug: string;
  logo_url?: string;
}

export interface Step2Data {
  description?: string;
  website?: string;
  industry?: string;
  company_size?: string;
  founded_year?: number;
  headquarters?: string;
  tax_id?: string;
  phone?: string;
  address?: string;
}

export interface Step3Data {
  expertise_areas: string[];
  custom_expertise?: string;
  annual_tender_volume?: string;
  average_contract_value?: string;
  target_regions: string[];
  certifications: string[];
}

export interface Step4Data {
  plan_id: string;
  billing_cycle: string;
  addons?: string[];
}

export interface Step5Data {
  notifications_enabled: boolean;
  email_digest: string;
  timezone: string;
  currency: string;
  language: string;
  widgets?: { id: string; type: string; enabled: boolean; position: number }[];
}

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

export interface Step1Response {
  success: boolean;
  step: number;
  completed: boolean;
  tenant_id: string;
  tenant_name: string;
  onboarding_state: OnboardingApiResponse;
  session?: OnboardingSessionPayload;
}

export interface Step2Response {
  success: boolean;
  step: number;
  completed: boolean;
  onboarding_state: OnboardingApiResponse;
}

export interface Step3Response {
  success: boolean;
  step: number;
  completed: boolean;
  onboarding_state: OnboardingApiResponse;
}

export interface Step4Response {
  success: boolean;
  step: number;
  completed: boolean;
  plan_id: string;
  billing_cycle: string;
  onboarding_state: OnboardingApiResponse;
}

export interface Step5Response {
  success: boolean;
  step: number;
  completed: boolean;
  is_onboarding_complete: boolean;
  onboarding_state: OnboardingApiResponse;
  session?: OnboardingSessionPayload;
}

function syncFromApiState(
  store: ReturnType<typeof useOnboardingStore.getState>,
  state: OnboardingApiResponse,
  extras?: { tenantName?: string }
) {
  const patch = mapOnboardingState(state);
  store.syncFromServer({
    ...patch,
    tenantName: extras?.tenantName ?? patch.tenantName,
  });
}

export function useOnboardingApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const store = useOnboardingStore();

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<OnboardingApiResponse>('/api/v1/onboarding/status');
      syncFromApiState(store, res);
      return res;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch onboarding status';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [store]);

  const submitStep1 = useCallback(async (data: Step1Data): Promise<Step1Response> => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post<Step1Response>('/api/v1/onboarding/step/1', data);
      syncFromApiState(store, res.onboarding_state, { tenantName: res.tenant_name });
      applyOnboardingSession(res.session, res.tenant_id);
      store.setStepCompleted(1, true);
      store.setTenantInfo(res.tenant_id, res.tenant_name);
      return res;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create organization';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [store]);

  const submitStep2 = useCallback(async (data: Step2Data): Promise<Step2Response> => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post<Step2Response>('/api/v1/onboarding/step/2', data);
      syncFromApiState(store, res.onboarding_state);
      store.setStepCompleted(2, true);
      return res;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to save profile';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [store]);

  const submitStep3 = useCallback(async (data: Step3Data): Promise<Step3Response> => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post<Step3Response>('/api/v1/onboarding/step/3', data);
      syncFromApiState(store, res.onboarding_state);
      store.setStepCompleted(3, true);
      return res;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to save expertise';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [store]);

  const submitStep4 = useCallback(async (data: Step4Data): Promise<Step4Response> => {
    setLoading(true);
    setError(null);
    try {
      const payload = normalizeOnboardingStep4(data);
      const res = await api.post<Step4Response>('/api/v1/onboarding/step/4', payload);
      syncFromApiState(store, res.onboarding_state);
      store.setStepCompleted(4, true);
      return res;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to select plan';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [store]);

  const submitStep5 = useCallback(async (data: Step5Data): Promise<Step5Response> => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post<Step5Response>('/api/v1/onboarding/step/5', data);
      syncFromApiState(store, res.onboarding_state);
      store.setStepCompleted(5, true);
      store.setOnboardingComplete(true);
      applyOnboardingSession(res.session, res.onboarding_state.tenant_id);
      return res;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to setup dashboard';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [store]);

  const fetchPlans = useCallback(async (): Promise<Plan[]> => {
    const res = await api.get<{ plans: Plan[] }>('/api/v1/onboarding/plans');
    return parsePlansResponse(res);
  }, []);

  const fetchExpertiseCategories = useCallback(async (): Promise<ExpertiseCategory> => {
    return api.get<ExpertiseCategory>('/api/v1/onboarding/expertise-categories');
  }, []);

  return {
    loading,
    error,
    fetchStatus,
    submitStep1,
    submitStep2,
    submitStep3,
    submitStep4,
    submitStep5,
    fetchPlans,
    fetchExpertiseCategories,
  };
}

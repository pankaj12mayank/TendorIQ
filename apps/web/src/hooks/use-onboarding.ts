import { useCallback, useState } from 'react';
import { api } from '@/lib/api';
import { useOnboardingStore, Plan, ExpertiseCategory } from '@/stores/onboarding-store';

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
      store.syncFromServer({
        currentStep: res.current_step,
        step1Completed: res.step_1_completed,
        step2Completed: res.step_2_completed,
        step3Completed: res.step_3_completed,
        step4Completed: res.step_4_completed,
        step5Completed: res.step_5_completed,
        step1Data: res.step_1_data,
        step2Data: res.step_2_data,
        step3Data: res.step_3_data,
        step4Data: res.step_4_data,
        step5Data: res.step_5_data,
        isCompleted: res.is_completed,
        tenantId: res.tenant_id ?? null,
      });
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
      store.syncFromServer({
        step1Completed: true,
        currentStep: 2,
        step1Data: data,
        tenantId: res.tenant_id,
        tenantName: res.tenant_name,
      });
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
      store.syncFromServer({
        step2Completed: true,
        currentStep: 3,
        step2Data: data,
      });
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
      store.syncFromServer({
        step3Completed: true,
        currentStep: 4,
        step3Data: data,
      });
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
      const res = await api.post<Step4Response>('/api/v1/onboarding/step/4', data);
      store.syncFromServer({
        step4Completed: true,
        currentStep: 5,
        step4Data: data,
      });
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
      store.syncFromServer({
        step5Completed: true,
        isCompleted: true,
        step5Data: data,
      });
      store.setStepCompleted(5, true);
      store.setOnboardingComplete(true);
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
    return res.plans;
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
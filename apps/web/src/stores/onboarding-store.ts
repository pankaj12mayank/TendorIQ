import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface OnboardingState {
  currentStep: number;
  totalSteps: number;
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
  isLoading: boolean;
  error: string | null;
  setCurrentStep: (step: number) => void;
  setStepCompleted: (step: number, completed: boolean) => void;
  setStepData: (step: number, data: Record<string, unknown>) => void;
  setTenantInfo: (id: string, name: string) => void;
  setOnboardingComplete: (completed: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  syncFromServer: (state: Partial<OnboardingState>) => void;
  reset: () => void;
}

const initialState = {
  currentStep: 1,
  totalSteps: 5,
  step1Completed: false,
  step2Completed: false,
  step3Completed: false,
  step4Completed: false,
  step5Completed: false,
  step1Data: {},
  step2Data: {},
  step3Data: {},
  step4Data: {},
  step5Data: {},
  isCompleted: false,
  tenantId: null,
  tenantName: null,
  isLoading: false,
  error: null,
};

export const useOnboardingStore = create<OnboardingState>()(
  persist(
    (set) => ({
      ...initialState,

      setCurrentStep: (step) => set({ currentStep: step }),

      setStepCompleted: (step, completed) => {
        const updates: Partial<OnboardingState> = {};
        switch (step) {
          case 1: updates.step1Completed = completed; break;
          case 2: updates.step2Completed = completed; break;
          case 3: updates.step3Completed = completed; break;
          case 4: updates.step4Completed = completed; break;
          case 5: updates.step5Completed = completed; break;
        }
        if (completed) {
          updates.currentStep = step + 1;
        }
        set(updates);
      },

      setStepData: (step, data) => {
        const updates: Partial<OnboardingState> = {};
        switch (step) {
          case 1: updates.step1Data = { ...updates.step1Data, ...data }; break;
          case 2: updates.step2Data = { ...updates.step2Data, ...data }; break;
          case 3: updates.step3Data = { ...updates.step3Data, ...data }; break;
          case 4: updates.step4Data = { ...updates.step4Data, ...data }; break;
          case 5: updates.step5Data = { ...updates.step5Data, ...data }; break;
        }
        set(updates);
      },

      setTenantInfo: (id, name) => set({ tenantId: id, tenantName: name }),

      setOnboardingComplete: (completed) => set({ isCompleted: completed }),

      setLoading: (loading) => set({ isLoading: loading }),

      setError: (error) => set({ error }),

      syncFromServer: (state) => set({
        currentStep: state.currentStep ?? 1,
        step1Completed: state.step1Completed ?? false,
        step2Completed: state.step2Completed ?? false,
        step3Completed: state.step3Completed ?? false,
        step4Completed: state.step4Completed ?? false,
        step5Completed: state.step5Completed ?? false,
        step1Data: state.step1Data ?? {},
        step2Data: state.step2Data ?? {},
        step3Data: state.step3Data ?? {},
        step4Data: state.step4Data ?? {},
        step5Data: state.step5Data ?? {},
        isCompleted: state.isCompleted ?? false,
        tenantId: state.tenantId ?? null,
      }),

      reset: () => set(initialState),
    }),
    {
      name: 'onboarding-storage',
      partialize: (state) => ({
        currentStep: state.currentStep,
        step1Completed: state.step1Completed,
        step2Completed: state.step2Completed,
        step3Completed: state.step3Completed,
        step4Completed: state.step4Completed,
        step5Completed: state.step5Completed,
        step1Data: state.step1Data,
        step2Data: state.step2Data,
        step3Data: state.step3Data,
        step4Data: state.step4Data,
        step5Data: state.step5Data,
        isCompleted: state.isCompleted,
        tenantId: state.tenantId,
        tenantName: state.tenantName,
      }),
    }
  )
);

export interface Plan {
  id: string;
  name: string;
  description: string;
  price_monthly: number;
  price_yearly: number;
  currency: string;
  features: { name: string; included: boolean; limit?: string }[];
  recommended: boolean;
}

export interface ExpertiseCategory {
  expertise_areas: string[];
  industries: string[];
  company_sizes: string[];
  annual_tender_volumes: string[];
  average_contract_values: string[];
  target_regions: { id: string; name: string }[];
  certifications: string[];
}
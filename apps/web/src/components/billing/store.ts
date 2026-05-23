import { create } from 'zustand';
import { api } from '@/lib/api-client';
import {
  mapQuotaFromUsageApi,
  mapSubscriptionFromApi,
  parsePaymentMethodsResponse,
} from '@/lib/billing-api';
import {
  Plan,
  Subscription,
  Invoice,
  PaymentMethod,
  QuotaStatus,
  BillingInterval,
} from './types';


interface BillingState {
  plans: Plan[];
  currentSubscription: Subscription | null;
  invoices: Invoice[];
  paymentMethods: PaymentMethod[];
  quotaStatus: QuotaStatus[];
  isLoading: boolean;
  isProcessing: boolean;
  error: string | null;

  setSubscription: (subscription: Subscription | null) => void;
  setPlans: (plans: Plan[]) => void;
  setInvoices: (invoices: Invoice[]) => void;
  setPaymentMethods: (methods: PaymentMethod[]) => void;
  setQuotaStatus: (quota: QuotaStatus[]) => void;
  setLoading: (loading: boolean) => void;
  setProcessing: (processing: boolean) => void;
  setError: (error: string | null) => void;

  changePlan: (planId: string, billingInterval: BillingInterval) => Promise<void>;
  cancelSubscription: (reason?: string) => Promise<void>;
  reactivateSubscription: () => Promise<void>;
  updatePaymentMethod: (methodId: string, isDefault: boolean) => Promise<void>;
  addPaymentMethod: (method: PaymentMethod) => Promise<void>;
  removePaymentMethod: (methodId: string) => Promise<void>;
  refreshQuota: () => Promise<void>;
}

export const useBillingStore = create<BillingState>((set, get) => ({
  plans: [],
  currentSubscription: null,
  invoices: [],
  paymentMethods: [],
  quotaStatus: [],
  isLoading: false,
  isProcessing: false,
  error: null,

  setSubscription: (subscription) => set({ currentSubscription: subscription }),
  setPlans: (plans) => set({ plans }),
  setInvoices: (invoices) => set({ invoices }),
  setPaymentMethods: (methods) => set({ paymentMethods: methods }),
  setQuotaStatus: (quota) => set({ quotaStatus: quota }),
  setLoading: (loading) => set({ isLoading: loading }),
  setProcessing: (processing) => set({ isProcessing: processing }),
  setError: (error) => set({ error }),

  changePlan: async (planId: string, billingInterval: BillingInterval) => {
    set({ isProcessing: true, error: null });
    try {
      const res = await api.post<{ subscription?: Subscription }>(
        '/api/v1/billing/subscription/change',
        { plan_id: planId, billing_interval: billingInterval }
      );
      if (res.subscription) {
        set({ currentSubscription: mapSubscriptionFromApi(res.subscription), isProcessing: false });
      } else {
        const sub = await api.get<Subscription>('/api/v1/billing/subscription');
        set({ currentSubscription: mapSubscriptionFromApi(sub), isProcessing: false });
      }
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Plan change failed', isProcessing: false });
    }
  },

  cancelSubscription: async (reason?: string) => {
    set({ isProcessing: true, error: null });
    try {
      const res = await api.post<{ subscription: Subscription }>(
        '/api/v1/billing/subscription/cancel',
        { reason }
      );
      set({ currentSubscription: mapSubscriptionFromApi(res.subscription), isProcessing: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Cancellation failed', isProcessing: false });
    }
  },

  reactivateSubscription: async () => {
    set({ isProcessing: true, error: null });
    try {
      const res = await api.post<{ subscription: Subscription }>('/api/v1/billing/subscription/reactivate');
      set({ currentSubscription: mapSubscriptionFromApi(res.subscription), isProcessing: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Reactivation failed', isProcessing: false });
    }
  },

  updatePaymentMethod: async (methodId: string, isDefault: boolean) => {
    set({ isProcessing: true, error: null });
    try {
      await api.patch(`/api/v1/billing/payment-methods/${methodId}`, { is_default: isDefault });
      const res = await api.get<unknown>('/api/v1/billing/payment-methods');
      set({ paymentMethods: parsePaymentMethodsResponse(res), isProcessing: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Update failed', isProcessing: false });
    }
  },

  addPaymentMethod: async (method: PaymentMethod) => {
    set({ isProcessing: true, error: null });
    try {
      await api.post('/api/v1/billing/payment-methods', method);
      const res = await api.get<unknown>('/api/v1/billing/payment-methods');
      set({ paymentMethods: parsePaymentMethodsResponse(res), isProcessing: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Add failed', isProcessing: false });
    }
  },

  removePaymentMethod: async (methodId: string) => {
    set({ isProcessing: true, error: null });
    try {
      await api.delete(`/api/v1/billing/payment-methods/${methodId}`);
      const res = await api.get<unknown>('/api/v1/billing/payment-methods');
      set({ paymentMethods: parsePaymentMethodsResponse(res), isProcessing: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Remove failed', isProcessing: false });
    }
  },

  refreshQuota: async () => {
    set({ isLoading: true });
    try {
      const data = await api.get<{ quotas?: QuotaStatus[]; quota?: QuotaStatus[] }>('/api/v1/billing/quota');
      set({ quotaStatus: mapQuotaFromUsageApi(data), isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },
}));
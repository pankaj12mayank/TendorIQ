import { useCallback, useState } from 'react';
import { api } from '@/lib/api-client';
import { useBillingStore } from '@/components/billing/store';
import {
  parsePlansResponse,
  mapQuotaFromUsageApi,
  mapSubscriptionFromApi,
  parseInvoicesResponse,
  parsePaymentMethodsResponse,
} from '@/lib/billing-api';
import {
  Plan,
  Subscription,
  Invoice,
  PaymentMethod,
  QuotaStatus,
  BillingInterval,
  PlanChangeResult,
} from '@/components/billing/types';

interface UseBillingApiReturn {
  plans: Plan[];
  currentSubscription: Subscription | null;
  invoices: Invoice[];
  paymentMethods: PaymentMethod[];
  quotaStatus: QuotaStatus[];
  isLoading: boolean;
  isProcessing: boolean;
  error: string | null;

  fetchPlans: () => Promise<void>;
  fetchSubscription: () => Promise<Subscription>;
  fetchInvoices: () => Promise<Invoice[]>;
  fetchQuotaStatus: () => Promise<QuotaStatus[]>;
  fetchPaymentHistory: (params?: {
    page?: number;
    limit?: number;
    status?: string;
    provider?: string;
  }) => Promise<{
    items: Array<{
      id: string;
      payment_date: string | null;
      amount: number;
      currency: string;
      status: string;
      provider: string;
      invoice: string;
      plan?: string | null;
      expiry?: string | null;
    }>;
    pagination: { page: number; limit: number; total: number; pages: number };
  }>;

  createSubscription: (planId: string, billingInterval: BillingInterval, paymentMethodId: string) => Promise<Subscription>;
  changePlan: (planId: string, billingInterval: BillingInterval) => Promise<PlanChangeResult>;
  cancelSubscription: (reason?: string) => Promise<void>;
  reactivateSubscription: () => Promise<void>;

  updatePaymentMethod: (methodId: string, isDefault: boolean) => Promise<void>;
  addPaymentMethod: (token: string) => Promise<PaymentMethod>;
  removePaymentMethod: (methodId: string) => Promise<void>;

  getPlanById: (planId: string) => Plan | undefined;
  getUpgradeOptions: () => Plan[];
  getDowngradeOptions: () => Plan[];
  canUpgrade: (planId: string) => boolean;
  canDowngrade: (planId: string) => boolean;
  initialize: () => Promise<void>;
}

export function useBillingApi(): UseBillingApiReturn {
  const plans = useBillingStore((s) => s.plans);
  const currentSubscription = useBillingStore((s) => s.currentSubscription);
  const invoices = useBillingStore((s) => s.invoices);
  const paymentMethods = useBillingStore((s) => s.paymentMethods);
  const quotaStatus = useBillingStore((s) => s.quotaStatus);
  const setPlans = useBillingStore((s) => s.setPlans);
  const setSubscription = useBillingStore((s) => s.setSubscription);
  const setInvoices = useBillingStore((s) => s.setInvoices);
  const setPaymentMethods = useBillingStore((s) => s.setPaymentMethods);
  const setQuotaStatus = useBillingStore((s) => s.setQuotaStatus);
  const [isLoading, setLoading] = useState(false);
  const [isProcessing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPlans = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<unknown>('/api/v1/billing/plans');
      const plans = parsePlansResponse(res);
      setPlans(plans);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch plans');
    } finally {
      setLoading(false);
    }
  }, [setPlans]);

  const fetchSubscription = useCallback(async (): Promise<Subscription> => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<Subscription>('/api/v1/billing/subscription');
      const sub = mapSubscriptionFromApi(res);
      setSubscription(sub);
      return sub;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch subscription');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [setSubscription]);

  const fetchInvoices = useCallback(async (): Promise<Invoice[]> => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<unknown>('/api/v1/billing/invoices');
      const invoices = parseInvoicesResponse(res);
      setInvoices(invoices);
      return invoices;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch invoices');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [setInvoices]);

  const fetchQuotaStatus = useCallback(async (): Promise<QuotaStatus[]> => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<{ quota?: QuotaStatus[]; quotas?: QuotaStatus[] }>(
        '/api/v1/billing/quota'
      );
      const quota = mapQuotaFromUsageApi(res);
      setQuotaStatus(quota);
      return quota;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch quota');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [setQuotaStatus]);

  const fetchPaymentHistory = useCallback(
    async (params?: { page?: number; limit?: number; status?: string; provider?: string }) => {
      try {
        const qs = new URLSearchParams();
        Object.entries(params ?? {}).forEach(([k, v]) => {
          if (v !== undefined && v !== null && String(v) !== '') qs.set(k, String(v));
        });
        const res = await api.get<{ items: any[]; pagination: any }>(
          `/api/v1/billing/payments/history${qs.toString() ? `?${qs}` : ''}`
        );
        const data = (res as any)?.data ?? res;
        return {
          items: data.items ?? [],
          pagination: data.pagination ?? { page: 1, limit: 20, total: 0, pages: 0 },
        };
      } catch {
        return {
          items: [],
          pagination: { page: 1, limit: 20, total: 0, pages: 0 },
        };
      }
    },
    []
  );

  const initialize = useCallback(async () => {
    await Promise.allSettled([fetchPlans(), fetchSubscription(), fetchQuotaStatus(), fetchInvoices()]);
  }, [fetchPlans, fetchSubscription, fetchQuotaStatus, fetchInvoices]);

  const createSubscription = useCallback(
    async (planId: string, billingInterval: BillingInterval, _paymentMethodId: string) => {
      setProcessing(true);
      setError(null);
      try {
        const res = await api.post<{ subscription: Subscription }>('/api/v1/billing/upgrade', {
          plan_id: planId,
          billing_interval: billingInterval,
        });
        const sub = mapSubscriptionFromApi((res as { subscription: Subscription }).subscription ?? res);
        setSubscription(sub);
        return sub;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to create subscription');
        throw err;
      } finally {
        setProcessing(false);
      }
    },
    [setSubscription]
  );

  const changePlan = useCallback(
    async (planId: string, billingInterval: BillingInterval): Promise<PlanChangeResult> => {
      setProcessing(true);
      setError(null);
      try {
        const res = await api.post<PlanChangeResult & { subscription?: Subscription }>(
          '/api/v1/billing/subscription/change',
          { plan_id: planId, billing_interval: billingInterval }
        );
        if (res.subscription) {
          setSubscription(mapSubscriptionFromApi(res.subscription));
        } else {
          await fetchSubscription();
        }
        await fetchQuotaStatus();
        return { ...res, success: true };
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to change plan';
        setError(message);
        return { success: false, error: message };
      } finally {
        setProcessing(false);
      }
    },
    [setSubscription, fetchSubscription, fetchQuotaStatus]
  );

  const cancelSubscription = useCallback(
    async (reason?: string) => {
      setProcessing(true);
      setError(null);
      try {
        const res = await api.post<{ subscription: Subscription }>('/api/v1/billing/subscription/cancel', {
          reason,
        });
        setSubscription(mapSubscriptionFromApi(res.subscription));
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to cancel subscription');
      } finally {
        setProcessing(false);
      }
    },
    [setSubscription]
  );

  const reactivateSubscription = useCallback(async () => {
    setProcessing(true);
    setError(null);
    try {
      const res = await api.post<{ subscription: Subscription }>('/api/v1/billing/subscription/reactivate');
      setSubscription(mapSubscriptionFromApi(res.subscription));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reactivate subscription');
    } finally {
      setProcessing(false);
    }
  }, [setSubscription]);

  const updatePaymentMethod = useCallback(
    async (methodId: string, isDefault: boolean) => {
      setProcessing(true);
      try {
        await api.patch(`/api/v1/billing/payment-methods/${methodId}`, { is_default: isDefault });
        const res = await api.get<unknown>('/api/v1/billing/payment-methods');
        setPaymentMethods(parsePaymentMethodsResponse(res));
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to update payment method');
      } finally {
        setProcessing(false);
      }
    },
    [setPaymentMethods]
  );

  const addPaymentMethod = useCallback(
    async (token: string): Promise<PaymentMethod> => {
      setProcessing(true);
      try {
        const res = await api.post<PaymentMethod>('/api/v1/billing/payment-methods', { token });
        const pmRes = await api.get<unknown>('/api/v1/billing/payment-methods');
        setPaymentMethods(parsePaymentMethodsResponse(pmRes));
        return res;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to add payment method');
        throw err;
      } finally {
        setProcessing(false);
      }
    },
    [setPaymentMethods]
  );

  const removePaymentMethod = useCallback(
    async (methodId: string) => {
      setProcessing(true);
      try {
        await api.delete(`/api/v1/billing/payment-methods/${methodId}`);
        const res = await api.get<unknown>('/api/v1/billing/payment-methods');
        setPaymentMethods(parsePaymentMethodsResponse(res));
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to remove payment method');
      } finally {
        setProcessing(false);
      }
    },
    [setPaymentMethods]
  );

  const getPlanById = useCallback((planId: string) => plans.find((p) => p.id === planId), [plans]);

  const getUpgradeOptions = useCallback(() => {
    const currentPlan = currentSubscription?.plan;
    if (!currentPlan) return plans.filter((p) => p.isActive);
    const currentIndex = plans.findIndex((p) => p.id === currentPlan.id);
    return plans.slice(currentIndex + 1).filter((p) => p.isActive);
  }, [currentSubscription, plans]);

  const getDowngradeOptions = useCallback(() => {
    const currentPlan = currentSubscription?.plan;
    if (!currentPlan) return [];
    const currentIndex = plans.findIndex((p) => p.id === currentPlan.id);
    return plans.slice(0, currentIndex).filter((p) => p.isActive).reverse();
  }, [currentSubscription, plans]);

  const canUpgrade = useCallback((planId: string) => getUpgradeOptions().some((p) => p.id === planId), [getUpgradeOptions]);
  const canDowngrade = useCallback(
    (planId: string) => getDowngradeOptions().some((p) => p.id === planId),
    [getDowngradeOptions]
  );

  return {
    plans,
    currentSubscription,
    invoices,
    paymentMethods,
    quotaStatus,
    isLoading,
    isProcessing,
    error,
    fetchPlans,
    fetchSubscription,
    fetchInvoices,
    fetchQuotaStatus,
    fetchPaymentHistory,
    createSubscription,
    changePlan,
    cancelSubscription,
    reactivateSubscription,
    updatePaymentMethod,
    addPaymentMethod,
    removePaymentMethod,
    getPlanById,
    getUpgradeOptions,
    getDowngradeOptions,
    canUpgrade,
    canDowngrade,
    initialize,
  };
}

interface UseQuotaEnforcementReturn {
  checkQuota: (featureKey: string, amount: number) => { allowed: boolean; remaining: number };
  getQuotaStatus: (featureKey: string) => QuotaStatus | undefined;
  getAllQuotaStatus: () => QuotaStatus[];
  canPerformAction: (featureKey: string) => boolean;
  getUpgradePrompt: (featureKey: string) => string | null;
}

export function useQuotaEnforcement(): UseQuotaEnforcementReturn {
  const { quotaStatus, currentSubscription } = useBillingStore();

  const checkQuota = useCallback(
    (featureKey: string, amount: number) => {
      const quota = quotaStatus.find((q) => q.featureKey === featureKey);
      if (!quota) return { allowed: true, remaining: Infinity };
      if (quota.isUnlimited) return { allowed: true, remaining: Infinity };
      const allowed = quota.remaining !== null && quota.remaining >= amount;
      return { allowed, remaining: quota.remaining ?? 0 };
    },
    [quotaStatus]
  );

  const getQuotaStatus = useCallback(
    (featureKey: string) => quotaStatus.find((q) => q.featureKey === featureKey),
    [quotaStatus]
  );

  const getAllQuotaStatus = useCallback(() => quotaStatus, [quotaStatus]);

  const canPerformAction = useCallback(
    (featureKey: string) => checkQuota(featureKey, 1).allowed,
    [checkQuota]
  );

  const getUpgradePrompt = useCallback(
    (featureKey: string) => {
      const quota = getQuotaStatus(featureKey);
      if (!quota || quota.isUnlimited || quota.remaining === null) return null;
      if (quota.remaining <= 0) {
        return `You've reached your ${quota.featureName} limit. Upgrade for more capacity.`;
      }
      if (quota.remaining < 10) {
        return `Only ${quota.remaining} ${quota.featureName} remaining. Consider upgrading.`;
      }
      return null;
    },
    [getQuotaStatus]
  );

  return {
    checkQuota,
    getQuotaStatus,
    getAllQuotaStatus,
    canPerformAction,
    getUpgradePrompt,
  };
}

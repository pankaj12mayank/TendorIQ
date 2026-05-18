import { useCallback, useState } from 'react';
import { useBillingStore } from '@/components/billing/store';
import { 
  Plan, 
  Subscription, 
  Invoice, 
  PaymentMethod, 
  QuotaStatus,
  BillingInterval,
  PlanChangeResult
} from '@/components/billing/types';
import { PLANS, MOCK_SUBSCRIPTION, MOCK_INVOICES, MOCK_QUOTA_STATUS } from '@/components/billing/constants';

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
}

export function useBillingApi(): UseBillingApiReturn {
  const store = useBillingStore();
  const [isLoading, setLoading] = useState(false);
  const [isProcessing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPlans = useCallback(async () => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    store.setPlans(PLANS);
    setLoading(false);
  }, []);

  const fetchSubscription = useCallback(async (): Promise<Subscription> => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    store.setSubscription(MOCK_SUBSCRIPTION);
    setLoading(false);
    return MOCK_SUBSCRIPTION;
  }, []);

  const fetchInvoices = useCallback(async (): Promise<Invoice[]> => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    store.setInvoices(MOCK_INVOICES);
    setLoading(false);
    return MOCK_INVOICES;
  }, []);

  const fetchQuotaStatus = useCallback(async (): Promise<QuotaStatus[]> => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    store.setQuotaStatus(MOCK_QUOTA_STATUS);
    setLoading(false);
    return MOCK_QUOTA_STATUS;
  }, []);

  const createSubscription = useCallback(async (
    planId: string,
    billingInterval: BillingInterval,
    paymentMethodId: string
  ): Promise<Subscription> => {
    setProcessing(true);
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    const plan = PLANS.find(p => p.id === planId);
    if (!plan) {
      setError('Plan not found');
      setProcessing(false);
      throw new Error('Plan not found');
    }

    const newSubscription: Subscription = {
      id: `sub_${Date.now()}`,
      userId: 'user_123',
      planId: plan.id,
      plan,
      status: 'active',
      billingInterval,
      stripeSubscriptionId: `sub_stripe_${Date.now()}`,
      stripeCustomerId: 'cus_stripe_456',
      currentPeriodStart: new Date().toISOString(),
      currentPeriodEnd: new Date(Date.now() + (billingInterval === 'monthly' ? 30 : 365) * 24 * 60 * 60 * 1000).toISOString(),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    store.setSubscription(newSubscription);
    setProcessing(false);
    return newSubscription;
  }, []);

  const changePlan = useCallback(async (
    planId: string,
    billingInterval: BillingInterval
  ): Promise<PlanChangeResult> => {
    setProcessing(true);
    await new Promise(resolve => setTimeout(resolve, 1500));

    const currentPlan = store.currentSubscription?.plan;
    const newPlan = PLANS.find(p => p.id === planId);

    if (!currentPlan || !newPlan) {
      setError('Invalid plan');
      setProcessing(false);
      return { success: false, error: 'Invalid plan' };
    }

    const currentPlanIndex = PLANS.findIndex(p => p.id === currentPlan.id);
    const newPlanIndex = PLANS.findIndex(p => p.id === planId);
    const isUpgrade = newPlanIndex > currentPlanIndex;

    const prorationAmount = isUpgrade
      ? (newPlan.priceMonthly - currentPlan.priceMonthly) / 2
      : 0;

    const newSubscription: Subscription = {
      ...store.currentSubscription!,
      planId: newPlan.id,
      plan: newPlan,
      billingInterval,
      updatedAt: new Date().toISOString(),
    };

    store.setSubscription(newSubscription);
    setProcessing(false);

    return {
      success: true,
      prorationAmount,
      immediateCharge: isUpgrade,
      nextBillingDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
    };
  }, []);

  const cancelSubscription = useCallback(async (reason?: string) => {
    setProcessing(true);
    await new Promise(resolve => setTimeout(resolve, 1000));

    if (!store.currentSubscription) {
      setError('No subscription found');
      setProcessing(false);
      return;
    }

    store.setSubscription({
      ...store.currentSubscription,
      status: 'canceled',
      canceledAt: new Date().toISOString(),
      cancelAtPeriodEnd: true,
    });

    setProcessing(false);
  }, []);

  const reactivateSubscription = useCallback(async () => {
    setProcessing(true);
    await new Promise(resolve => setTimeout(resolve, 1000));

    if (!store.currentSubscription) {
      setError('No subscription found');
      setProcessing(false);
      return;
    }

    store.setSubscription({
      ...store.currentSubscription,
      status: 'active',
      canceledAt: undefined,
      cancelAtPeriodEnd: false,
    });

    setProcessing(false);
  }, []);

  const updatePaymentMethod = useCallback(async (methodId: string, isDefault: boolean) => {
    setProcessing(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    
    const updatedMethods = store.paymentMethods.map(pm => ({
      ...pm,
      isDefault: pm.id === methodId ? isDefault : pm.isDefault,
    }));
    
    store.setPaymentMethods(updatedMethods);
    setProcessing(false);
  }, []);

  const addPaymentMethod = useCallback(async (token: string): Promise<PaymentMethod> => {
    setProcessing(true);
    await new Promise(resolve => setTimeout(resolve, 1000));

    const newMethod: PaymentMethod = {
      id: `pm_${Date.now()}`,
      userId: 'user_123',
      stripePaymentMethodId: token,
      type: 'card',
      brand: 'visa',
      last4: '1234',
      expiryMonth: 12,
      expiryYear: 2028,
      isDefault: store.paymentMethods.length === 0,
      isActive: true,
      createdAt: new Date().toISOString(),
    };

    store.setPaymentMethods([...store.paymentMethods, newMethod]);
    setProcessing(false);
    return newMethod;
  }, []);

  const removePaymentMethod = useCallback(async (methodId: string) => {
    setProcessing(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    
    store.setPaymentMethods(store.paymentMethods.filter(pm => pm.id !== methodId));
    setProcessing(false);
  }, []);

  const getPlanById = useCallback((planId: string) => {
    return PLANS.find(p => p.id === planId);
  }, []);

  const getUpgradeOptions = useCallback(() => {
    const currentPlan = store.currentSubscription?.plan;
    if (!currentPlan) return [];
    
    const currentIndex = PLANS.findIndex(p => p.id === currentPlan.id);
    return PLANS.slice(currentPlan ? currentIndex + 1 : 0).filter(p => p.isActive);
  }, [store.currentSubscription]);

  const getDowngradeOptions = useCallback(() => {
    const currentPlan = store.currentSubscription?.plan;
    if (!currentPlan) return [];
    
    const currentIndex = PLANS.findIndex(p => p.id === currentPlan.id);
    return PLANS.slice(0, currentIndex).filter(p => p.isActive).reverse();
  }, [store.currentSubscription]);

  const canUpgrade = useCallback((planId: string) => {
    return getUpgradeOptions().some(p => p.id === planId);
  }, [getUpgradeOptions]);

  const canDowngrade = useCallback((planId: string) => {
    return getDowngradeOptions().some(p => p.id === planId);
  }, [getDowngradeOptions]);

  return {
    plans: store.plans,
    currentSubscription: store.currentSubscription,
    invoices: store.invoices,
    paymentMethods: store.paymentMethods,
    quotaStatus: store.quotaStatus,
    isLoading,
    isProcessing,
    error,
    fetchPlans,
    fetchSubscription,
    fetchInvoices,
    fetchQuotaStatus,
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

  const checkQuota = useCallback((featureKey: string, amount: number) => {
    const quota = quotaStatus.find(q => q.featureKey === featureKey);
    if (!quota) return { allowed: true, remaining: Infinity };
    
    if (quota.isUnlimited) return { allowed: true, remaining: Infinity };
    
    const allowed = quota.remaining !== null && quota.remaining >= amount;
    return { allowed, remaining: quota.remaining ?? 0 };
  }, [quotaStatus]);

  const getQuotaStatus = useCallback((featureKey: string) => {
    return quotaStatus.find(q => q.featureKey === featureKey);
  }, [quotaStatus]);

  const getAllQuotaStatus = useCallback(() => {
    return quotaStatus;
  }, [quotaStatus]);

  const canPerformAction = useCallback((featureKey: string) => {
    const { allowed } = checkQuota(featureKey, 1);
    return allowed;
  }, [checkQuota]);

  const getUpgradePrompt = useCallback((featureKey: string) => {
    const quota = getQuotaStatus(featureKey);
    if (!quota || quota.isUnlimited || quota.remaining === null) return null;
    
    if (quota.remaining <= 0) {
      return `You've reached your ${quota.featureName} limit. Upgrade to Pro or Enterprise for more.`;
    }
    
    if (quota.remaining < 10) {
      return `Only ${quota.remaining} ${quota.featureName} remaining. Consider upgrading.`;
    }
    
    return null;
  }, [getQuotaStatus]);

  return {
    checkQuota,
    getQuotaStatus,
    getAllQuotaStatus,
    canPerformAction,
    getUpgradePrompt,
  };
}
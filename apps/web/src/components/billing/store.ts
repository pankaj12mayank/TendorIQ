import { create } from 'zustand';
import { 
  Plan, 
  Subscription, 
  Invoice, 
  PaymentMethod, 
  QuotaStatus,
  BillingInterval,
  PlanChangeType
} from './types';
import { PLANS, MOCK_SUBSCRIPTION, MOCK_INVOICES, MOCK_QUOTA_STATUS } from './constants';

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
  plans: PLANS,
  currentSubscription: MOCK_SUBSCRIPTION,
  invoices: MOCK_INVOICES,
  paymentMethods: [
    {
      id: 'pm_1',
      userId: 'user_123',
      stripePaymentMethodId: 'pm_stripe_123',
      type: 'card',
      brand: 'visa',
      last4: '4242',
      expiryMonth: 12,
      expiryYear: 2027,
      isDefault: true,
      isActive: true,
      createdAt: '2026-01-01T00:00:00Z',
    },
  ],
  quotaStatus: MOCK_QUOTA_STATUS,
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
    const { plans } = get();
    const newPlan = plans.find(p => p.id === planId);
    const currentSub = get().currentSubscription;

    if (!newPlan || !currentSub) {
      set({ error: 'Invalid plan or subscription' });
      return;
    }

    set({ isProcessing: true, error: null });

    await new Promise(resolve => setTimeout(resolve, 1500));

    const updatedSubscription: Subscription = {
      ...currentSub,
      planId: newPlan.id,
      plan: newPlan,
      billingInterval,
      updatedAt: new Date().toISOString(),
    };

    const invoice: Invoice = {
      id: `inv_${Date.now()}`,
      subscriptionId: currentSub.id,
      userId: currentSub.userId,
      invoiceNumber: `INV-${new Date().getFullYear()}-${String(get().invoices.length + 1).padStart(4, '0')}`,
      amount: billingInterval === 'monthly' ? newPlan.priceMonthly : newPlan.priceAnnual,
      currency: newPlan.currency,
      status: 'pending',
      description: `${newPlan.displayName} Plan - ${billingInterval === 'monthly' ? 'Monthly' : 'Annual'}`,
      dueDate: new Date().toISOString(),
      billingPeriodStart: new Date().toISOString(),
      billingPeriodEnd: new Date(Date.now() + (billingInterval === 'monthly' ? 30 : 365) * 24 * 60 * 60 * 1000).toISOString(),
      createdAt: new Date().toISOString(),
    };

    set(state => ({
      currentSubscription: updatedSubscription,
      invoices: [invoice, ...state.invoices],
      isProcessing: false,
    }));
  },

  cancelSubscription: async (reason?: string) => {
    set({ isProcessing: true, error: null });

    await new Promise(resolve => setTimeout(resolve, 1000));

    const currentSub = get().currentSubscription;
    if (!currentSub) {
      set({ error: 'No subscription found', isProcessing: false });
      return;
    }

    const updatedSubscription: Subscription = {
      ...currentSub,
      status: 'canceled',
      canceledAt: new Date().toISOString(),
      cancelAtPeriodEnd: true,
      updatedAt: new Date().toISOString(),
    };

    set(state => ({
      currentSubscription: updatedSubscription,
      isProcessing: false,
    }));
  },

  reactivateSubscription: async () => {
    set({ isProcessing: true, error: null });

    await new Promise(resolve => setTimeout(resolve, 1000));

    const currentSub = get().currentSubscription;
    if (!currentSub) {
      set({ error: 'No subscription found', isProcessing: false });
      return;
    }

    const updatedSubscription: Subscription = {
      ...currentSub,
      status: 'active',
      canceledAt: undefined,
      cancelAtPeriodEnd: false,
      updatedAt: new Date().toISOString(),
    };

    set(state => ({
      currentSubscription: updatedSubscription,
      isProcessing: false,
    }));
  },

  updatePaymentMethod: async (methodId: string, isDefault: boolean) => {
    set({ isProcessing: true, error: null });

    await new Promise(resolve => setTimeout(resolve, 500));

    set(state => ({
      paymentMethods: state.paymentMethods.map(pm =>
        pm.id === methodId ? { ...pm, isDefault } : pm
      ),
      isProcessing: false,
    }));
  },

  addPaymentMethod: async (method: PaymentMethod) => {
    set({ isProcessing: true, error: null });

    await new Promise(resolve => setTimeout(resolve, 1000));

    set(state => ({
      paymentMethods: [...state.paymentMethods, method],
      isProcessing: false,
    }));
  },

  removePaymentMethod: async (methodId: string) => {
    set({ isProcessing: true, error: null });

    await new Promise(resolve => setTimeout(resolve, 500));

    set(state => ({
      paymentMethods: state.paymentMethods.filter(pm => pm.id !== methodId),
      isProcessing: false,
    }));
  },

  refreshQuota: async () => {
    set({ isLoading: true });

    await new Promise(resolve => setTimeout(resolve, 800));

    set({ isLoading: false });
  },
}));
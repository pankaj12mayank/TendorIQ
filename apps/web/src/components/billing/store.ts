import { create } from 'zustand';
import { Plan, Subscription, Invoice, PaymentMethod, QuotaStatus } from './types';

/** UI state only — network calls live in `useBillingApi`. */
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
}

export const useBillingStore = create<BillingState>((set) => ({
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
}));

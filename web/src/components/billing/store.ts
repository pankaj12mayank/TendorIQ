import { create } from 'zustand';

import type { Invoice, PaymentMethod, Plan, QuotaStatus, Subscription } from './types';

interface BillingState {
  plans: Plan[];
  currentSubscription: Subscription | null;
  invoices: Invoice[];
  paymentMethods: PaymentMethod[];
  quotaStatus: QuotaStatus[];
  setPlans: (plans: Plan[]) => void;
  setSubscription: (sub: Subscription | null) => void;
  setInvoices: (invoices: Invoice[]) => void;
  setPaymentMethods: (methods: PaymentMethod[]) => void;
  setQuotaStatus: (quota: QuotaStatus[]) => void;
}

export const useBillingStore = create<BillingState>((set) => ({
  plans: [],
  currentSubscription: null,
  invoices: [],
  paymentMethods: [],
  quotaStatus: [],
  setPlans: (plans) => set({ plans }),
  setSubscription: (currentSubscription) => set({ currentSubscription }),
  setInvoices: (invoices) => set({ invoices }),
  setPaymentMethods: (paymentMethods) => set({ paymentMethods }),
  setQuotaStatus: (quotaStatus) => set({ quotaStatus }),
}));

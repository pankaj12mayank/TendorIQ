import { authenticatedFetch } from './api-fetch';
import { api } from './api-client';
import { unwrapData } from './api-envelope';

export interface RazorpayOrder {
  order_id: string;
  amount: number;
  currency: string;
  key_id: string;
  plan: string;
  plan_id: string;
  billing_interval: string;
}

export interface PaymentConfig {
  payment_enabled?: boolean;
  preferred_provider?: 'stripe' | 'razorpay' | null;
  razorpay_enabled: boolean;
  stripe_enabled?: boolean;
  stripe_publishable_key?: string | null;
  razorpay_key_id?: string;
  currency: string;
  providers?: string[];
}

declare global {
  interface Window {
    Razorpay?: new (options: Record<string, unknown>) => { open: () => void };
  }
}

export async function fetchPaymentConfig(): Promise<PaymentConfig> {
  const raw = await api.get<{ data?: PaymentConfig } | PaymentConfig>('/api/v1/payments/config');
  return unwrapData(raw as { data?: PaymentConfig }) as PaymentConfig;
}

export async function createRazorpayOrder(
  planId: string,
  billingInterval: 'monthly'
): Promise<RazorpayOrder> {
  const raw = await api.post<{ data?: RazorpayOrder } | RazorpayOrder>(
    '/api/v1/payments/razorpay/create-order',
    { plan_id: planId, billing_interval: billingInterval }
  );
  return unwrapData(raw as { data?: RazorpayOrder }) as RazorpayOrder;
}

export async function verifyRazorpayPayment(payload: {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
  plan_id: string;
  billing_interval: string;
}): Promise<unknown> {
  const raw = await api.post('/api/v1/payments/razorpay/verify', payload);
  return unwrapData(raw);
}

export function loadRazorpayScript(): Promise<void> {
  if (typeof window === 'undefined') return Promise.resolve();
  if (window.Razorpay) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const existing = document.getElementById('razorpay-checkout-js');
    if (existing) {
      existing.addEventListener('load', () => resolve());
      return;
    }
    const script = document.createElement('script');
    script.id = 'razorpay-checkout-js';
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Failed to load Razorpay checkout'));
    document.body.appendChild(script);
  });
}

export async function openRazorpayCheckout(
  order: RazorpayOrder,
  opts: { name?: string; email?: string; onSuccess?: () => void }
): Promise<void> {
  await loadRazorpayScript();
  if (!window.Razorpay) throw new Error('Razorpay SDK not available');

  return new Promise((resolve, reject) => {
    const rzp = new window.Razorpay!({
      key: order.key_id,
      amount: order.amount,
      currency: order.currency,
      name: 'TenderIQ',
      description: `${order.plan} plan`,
      order_id: order.order_id,
      prefill: { name: opts.name, email: opts.email },
      theme: { color: '#2563eb' },
      handler: async (response: {
        razorpay_payment_id: string;
        razorpay_order_id: string;
        razorpay_signature: string;
      }) => {
        try {
          await verifyRazorpayPayment({
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
            plan_id: order.plan_id,
            billing_interval: order.billing_interval,
          });
          opts.onSuccess?.();
          resolve();
        } catch (err) {
          reject(err);
        }
      },
      modal: {
        ondismiss: () => reject(new Error('Payment cancelled')),
      },
    });
    rzp.open();
  });
}

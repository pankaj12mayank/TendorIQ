import { api } from '@/lib/api-client';
import { unwrapData } from '@/lib/api-envelope';
import {
  createRazorpayOrder,
  fetchPaymentConfig,
  openRazorpayCheckout,
  type PaymentConfig,
} from '@/lib/razorpay-checkout';

export type { PaymentConfig };

export async function loadPaymentConfig(): Promise<PaymentConfig> {
  return fetchPaymentConfig();
}

async function payWithStripe(
  planId: string,
  billingInterval: 'monthly',
  urls: { successUrl: string; cancelUrl: string }
): Promise<void> {
  const raw = await api.post<{ checkout_url?: string; session_id?: string }>(
    '/api/v1/payments/stripe/create-checkout',
    {
      plan_id: planId,
      billing_interval: billingInterval,
      success_url: urls.successUrl,
      cancel_url: urls.cancelUrl,
    }
  );
  const body = unwrapData(raw) as { checkout_url?: string; session_id?: string };
  if (!body?.checkout_url) {
    throw new Error('Payment could not be started');
  }
  window.location.assign(body.checkout_url);
}

export async function confirmStripeReturn(sessionId: string): Promise<void> {
  await api.post('/api/v1/payments/stripe/confirm', { session_id: sessionId });
}

export async function payForPlan(
  planId: string,
  billingInterval: 'monthly',
  opts: {
    name?: string;
    email?: string;
    onSuccess?: () => void | Promise<void>;
    successUrl: string;
    cancelUrl: string;
  }
): Promise<void> {
  const config = await loadPaymentConfig();
  if (!config.payment_enabled) {
    throw new Error('Online payment is not available right now. Please try again later.');
  }

  if (config.preferred_provider === 'stripe' && config.stripe_enabled) {
    await payWithStripe(planId, billingInterval, {
      successUrl: opts.successUrl,
      cancelUrl: opts.cancelUrl,
    });
    return;
  }

  if (config.razorpay_enabled) {
    const order = await createRazorpayOrder(planId, billingInterval);
    await openRazorpayCheckout(order, {
      name: opts.name,
      email: opts.email,
      onSuccess: opts.onSuccess,
    });
    return;
  }

  throw new Error('Online payment is not available right now. Please try again later.');
}

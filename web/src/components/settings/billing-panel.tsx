'use client';

import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Check, CreditCard, Loader2, Sparkles } from 'lucide-react';
import { appToast } from '@/lib/app-toast';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useBillingApi } from '@/hooks/use-billing';
import { useSubscriptionAccess } from '@/hooks/use-subscription-access';
import { useCurrentUser } from '@/hooks/use-auth';
import {
  createRazorpayOrder,
  fetchPaymentConfig,
  openRazorpayCheckout,
} from '@/lib/razorpay-checkout';

type BillingInterval = 'yearly';

interface PlanCard {
  id: string;
  displayName?: string;
  description?: string;
  priceMonthlyInr?: number;
  priceAnnualInr?: number;
  isDemo?: boolean;
  features?: Array<{ name: string; limit?: number | null }>;
  name?: string;
}

export function BillingPanel() {
  const user = useCurrentUser();
  const searchParams = useSearchParams();
  const {
    plans,
    currentSubscription,
    initialize,
    isLoading,
    fetchSubscription,
    fetchQuotaStatus,
    fetchPaymentHistory,
  } = useBillingApi();
  const { data: access, refetch: refetchAccess } = useSubscriptionAccess();
  const [interval] = useState<BillingInterval>('yearly');
  const [payingPlanId, setPayingPlanId] = useState<string | null>(null);
  const [razorpayReady, setRazorpayReady] = useState<boolean | null>(null);
  const [payments, setPayments] = useState<Array<any>>([]);
  const [paymentsPage, setPaymentsPage] = useState(1);
  const [paymentStatus, setPaymentStatus] = useState('all');
  const [paymentPagination, setPaymentPagination] = useState({ page: 1, limit: 8, total: 0, pages: 0 });

  useEffect(() => {
    void initialize();
    void fetchPaymentConfig()
      .then((c) => setRazorpayReady(c.razorpay_enabled))
      .catch(() => setRazorpayReady(false));
  }, [initialize]);

  useEffect(() => {
    (async () => {
      const res = await fetchPaymentHistory({
        page: paymentsPage,
        limit: 8,
        status: paymentStatus === 'all' ? undefined : paymentStatus,
      });
      setPayments(res.items);
      setPaymentPagination(res.pagination);
    })();
  }, [fetchPaymentHistory, paymentsPage, paymentStatus]);

  useEffect(() => {
    if (searchParams.get('success') === 'true') {
      appToast.success('Payment successful.');
    }
  }, [searchParams]);

  const handleUpgrade = useCallback(
    async (plan: PlanCard) => {
      if (plan.isDemo) {
        appToast.info('You are on the free demo plan.');
        return;
      }
      setPayingPlanId(plan.id);
      try {
        const config = await fetchPaymentConfig();
        if (!config.razorpay_enabled) {
          appToast.error('Razorpay not configured. Add keys to .env and restart API.');
          return;
        }
        const order = await createRazorpayOrder(plan.id, interval);
        await openRazorpayCheckout(order, {
          name: user?.name,
          email: user?.email,
          onSuccess: async () => {
            appToast.success('Plan upgraded.');
            await fetchSubscription();
            await fetchQuotaStatus();
            await refetchAccess();
          },
        });
      } catch (err) {
        appToast.error(err instanceof Error ? err.message : 'Payment failed');
      } finally {
        setPayingPlanId(null);
      }
    },
    [interval, user, fetchSubscription, fetchQuotaStatus, refetchAccess]
  );

  const planList = (plans as unknown as PlanCard[]) ?? [];

  return (
    <div className="space-y-6 max-w-5xl">
      {access?.is_expired && (
        <Card className="border-destructive bg-destructive/5">
          <CardHeader>
            <CardTitle className="text-destructive">Plan expired</CardTitle>
            <CardDescription>
              {access.reason || 'Renew or upgrade below to restore uploads, AI, and exports.'}
            </CardDescription>
          </CardHeader>
        </Card>
      )}

      {currentSubscription && (
        <Card>
          <CardHeader>
            <CardTitle>Current subscription</CardTitle>
            <CardDescription>Yearly plan with real-time usage status</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">Current plan</p>
              <p className="font-semibold">{currentSubscription.plan?.displayName ?? currentSubscription.plan?.name}</p>
            </div>
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">Expiry date</p>
              <p className="font-semibold">
                {currentSubscription.currentPeriodEnd
                  ? new Date(currentSubscription.currentPeriodEnd).toLocaleDateString()
                  : '—'}
              </p>
            </div>
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">Status</p>
              <p className="font-semibold capitalize">{currentSubscription.status}</p>
            </div>
            {(currentSubscription.limits?.documents || currentSubscription.limits?.tenders) && (
              <div className="sm:col-span-3 rounded-lg border p-3 text-sm text-muted-foreground">
                {(currentSubscription.limits?.documents?.current ?? 0)} /{' '}
                {(currentSubscription.limits?.documents?.max ?? '∞')} documents used · remaining{' '}
                {currentSubscription.limits?.documents?.max != null
                  ? Math.max(
                      0,
                      (currentSubscription.limits.documents.max as number) -
                        (currentSubscription.limits.documents.current as number)
                    )
                  : '∞'}
              </div>
            )}
          </CardContent>
        </Card>
      )}
      <p className="text-xs text-muted-foreground">Yearly subscriptions only.</p>

      {razorpayReady === false && (
        <p className="text-sm text-amber-600">
          Razorpay keys missing in API `.env` — upgrades disabled until configured.
        </p>
      )}

      {isLoading ? (
        <div className="flex items-center gap-2 text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" /> Loading plans…
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-3">
          {planList.map((plan) => {
            if (plan.isDemo) return null;
            const price =
              interval === 'yearly'
                ? plan.priceAnnualInr ?? (plan.priceMonthlyInr ?? 0) * 10
                : plan.priceMonthlyInr ?? 0;
            const isCurrent = currentSubscription?.plan === (plan.name ?? plan.displayName);
            return (
              <Card key={plan.id} className={plan.isDemo ? 'border-dashed' : ''}>
                <CardHeader>
                  <CardTitle>{plan.displayName ?? plan.id}</CardTitle>
                  <CardDescription>{plan.description}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-2xl font-bold">
                    {`₹${price.toLocaleString('en-IN')}`}
                    {(
                      <span className="text-sm font-normal text-muted-foreground">
                        /yr
                      </span>
                    )}
                  </p>
                  <ul className="text-sm space-y-1 text-muted-foreground">
                    {(plan.features ?? []).slice(0, 4).map((f) => (
                      <li key={f.name} className="flex items-start gap-2">
                        <Check className="h-4 w-4 shrink-0 text-primary" />
                        {f.name}
                      </li>
                    ))}
                  </ul>
                  <Button
                    className="w-full"
                    variant="default"
                    disabled={isCurrent || payingPlanId === plan.id}
                    onClick={() => void handleUpgrade(plan)}
                  >
                    {payingPlanId === plan.id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : isCurrent ? (
                      'Current plan'
                    ) : (
                      <>
                        <CreditCard className="mr-2 h-4 w-4" />
                        Pay with Razorpay
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Payment history</CardTitle>
          <CardDescription>Your own payments only</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <Button size="sm" variant={paymentStatus === 'all' ? 'default' : 'outline'} onClick={() => setPaymentStatus('all')}>All</Button>
            <Button size="sm" variant={paymentStatus === 'paid' ? 'default' : 'outline'} onClick={() => setPaymentStatus('paid')}>Paid</Button>
            <Button size="sm" variant={paymentStatus === 'failed' ? 'default' : 'outline'} onClick={() => setPaymentStatus('failed')}>Failed</Button>
          </div>
          <div className="space-y-2">
            {payments.map((p) => (
              <div key={p.id} className="rounded-lg border p-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{p.plan ?? 'Plan'}</span>
                  <span className="capitalize">{p.status}</span>
                </div>
                <p className="text-muted-foreground">
                  {p.payment_date ? new Date(p.payment_date).toLocaleString() : '—'} · {p.provider} · {p.invoice}
                </p>
                <p>₹{Number(p.amount || 0).toLocaleString('en-IN')} {p.currency}</p>
              </div>
            ))}
            {payments.length === 0 && <p className="text-sm text-muted-foreground">No payments found.</p>}
          </div>
          {paymentPagination.pages > 1 && (
            <div className="flex items-center gap-2">
              <Button size="sm" variant="outline" disabled={paymentsPage <= 1} onClick={() => setPaymentsPage((p) => p - 1)}>Prev</Button>
              <span className="text-xs text-muted-foreground">{paymentsPage}/{paymentPagination.pages}</span>
              <Button size="sm" variant="outline" disabled={paymentsPage >= paymentPagination.pages} onClick={() => setPaymentsPage((p) => p + 1)}>Next</Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

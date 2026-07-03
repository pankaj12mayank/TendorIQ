'use client';

import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Check, CreditCard, Loader2 } from 'lucide-react';
import { appToast } from '@/lib/app-toast';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useBillingApi } from '@/hooks/use-billing';
import { useSubscriptionAccess } from '@/hooks/use-subscription-access';
import { useCurrentUser } from '@/hooks/use-auth';
import { confirmStripeReturn, payForPlan } from '@/lib/checkout';

type BillingInterval = 'monthly';

interface PlanCard {
  id: string;
  displayName?: string;
  description?: string;
  priceMonthlyUsd?: number;
  priceMonthlyInr?: number;
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
  const [interval] = useState<BillingInterval>('monthly');
  const [payingPlanId, setPayingPlanId] = useState<string | null>(null);
  const [payments, setPayments] = useState<Array<Record<string, unknown>>>([]);
  const [paymentsPage, setPaymentsPage] = useState(1);
  const [paymentStatus, setPaymentStatus] = useState('all');
  const [paymentPagination, setPaymentPagination] = useState({ page: 1, limit: 8, total: 0, pages: 0 });

  const billingBase = '/dashboard/billing';

  useEffect(() => {
    void initialize();
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

  const refreshBilling = useCallback(async () => {
    await fetchSubscription();
    await fetchQuotaStatus();
    await refetchAccess();
    setPaymentsPage(1);
  }, [fetchSubscription, fetchQuotaStatus, refetchAccess]);

  useEffect(() => {
    const sessionId = searchParams.get('session_id');
    if (searchParams.get('success') === 'true' && sessionId) {
      void (async () => {
        try {
          await confirmStripeReturn(sessionId);
          appToast.success('Payment successful. Your plan is active.');
          await refreshBilling();
        } catch (err) {
          appToast.error(err instanceof Error ? err.message : 'Could not confirm payment');
        }
      })();
      return;
    }
    if (searchParams.get('success') === 'true') {
      appToast.success('Payment successful.');
      void refreshBilling();
    }
  }, [searchParams, refreshBilling]);

  const handlePayNow = useCallback(
    async (plan: PlanCard) => {
      if (plan.isDemo) {
        appToast.info('This plan is not available.');
        return;
      }
      setPayingPlanId(plan.id);
      try {
        const origin = typeof window !== 'undefined' ? window.location.origin : '';
        await payForPlan(plan.id, interval, {
          name: user?.name,
          email: user?.email,
          successUrl: `${origin}${billingBase}&success=true&session_id={CHECKOUT_SESSION_ID}`,
          cancelUrl: `${origin}${billingBase}`,
          onSuccess: async () => {
            appToast.success('Plan activated.');
            await refreshBilling();
          },
        });
      } catch (err) {
        appToast.error(err instanceof Error ? err.message : 'Payment failed');
      } finally {
        setPayingPlanId(null);
      }
    },
    [interval, user, refreshBilling, billingBase]
  );

  const planList = (plans as unknown as PlanCard[]) ?? [];

  return (
    <div className="w-full space-y-6">
      {access && !access.can_use_system && (
        <Card className="border-destructive bg-destructive/5">
          <CardHeader>
            <CardTitle className="text-destructive">
              {access.plan === 'free' ? 'Subscription required' : 'Plan expired'}
            </CardTitle>
            <CardDescription>
              {access.reason || 'Purchase a plan below to use uploads, analysis, and proposals.'}
            </CardDescription>
          </CardHeader>
        </Card>
      )}

      {currentSubscription && currentSubscription.plan && access?.can_use_system && (
        <Card>
          <CardHeader>
            <CardTitle>Current subscription</CardTitle>
            <CardDescription>Monthly plan with usage limits</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-lg border p-3">
              <p className="text-xs text-muted-foreground">Current plan</p>
              <p className="font-semibold">
                {currentSubscription.plan?.displayName ?? currentSubscription.plan?.name}
              </p>
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
                {(currentSubscription.limits?.documents?.max ?? '∞')} documents used
              </div>
            )}
          </CardContent>
        </Card>
      )}
      <p className="text-xs text-muted-foreground">Monthly subscriptions only.</p>

      {isLoading ? (
        <div className="flex items-center gap-2 text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" /> Loading plans…
        </div>
      ) : planList.length === 0 ? (
        <p className="text-sm text-muted-foreground">No plans available yet.</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {planList.filter((p) => !p.isDemo).map((plan) => {
            const price = plan.priceMonthlyUsd ?? plan.priceMonthlyInr ?? 0;
            const isCurrent =
              currentSubscription?.plan?.name === (plan.name ?? plan.displayName) ||
              currentSubscription?.plan?.displayName === plan.displayName;
            return (
              <Card key={plan.id}>
                <CardHeader>
                  <CardTitle>{plan.displayName ?? plan.id}</CardTitle>
                  <CardDescription>{plan.description}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-2xl font-bold">
                    {`$${Number(price).toLocaleString('en-US')}`}
                    <span className="text-sm font-normal text-muted-foreground">/mo</span>
                  </p>
                  <ul className="text-sm space-y-1 text-muted-foreground">
                    {(plan.features ?? []).slice(0, 6).map((f: any) => (
                      <li key={typeof f === 'string' ? f : f.name} className="flex items-start gap-2">
                        <Check className="h-4 w-4 shrink-0 text-primary" />
                        {typeof f === 'string' ? f : f.name}
                      </li>
                    ))}
                  </ul>
                  <Button
                    className="w-full"
                    variant="default"
                    disabled={isCurrent || payingPlanId === plan.id}
                    onClick={() => void handlePayNow(plan)}
                  >
                    {payingPlanId === plan.id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : isCurrent ? (
                      'Current plan'
                    ) : (
                      <>
                        <CreditCard className="mr-2 h-4 w-4" />
                        Pay now
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
          <CardDescription>Your payments and plan renewals</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <Button
              size="sm"
              variant={paymentStatus === 'all' ? 'default' : 'outline'}
              onClick={() => setPaymentStatus('all')}
            >
              All
            </Button>
            <Button
              size="sm"
              variant={paymentStatus === 'paid' ? 'default' : 'outline'}
              onClick={() => setPaymentStatus('paid')}
            >
              Paid
            </Button>
            <Button
              size="sm"
              variant={paymentStatus === 'failed' ? 'default' : 'outline'}
              onClick={() => setPaymentStatus('failed')}
            >
              Failed
            </Button>
          </div>
          <div className="space-y-2">
            {payments.map((p) => (
              <div key={String(p.id)} className="rounded-lg border p-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{String(p.plan ?? 'Plan')}</span>
                  <span className="capitalize">{String(p.status)}</span>
                </div>
                <p className="text-muted-foreground">
                  {p.payment_date ? new Date(String(p.payment_date)).toLocaleString() : '—'}
                </p>
                <p>
                  ${Number(p.amount || 0).toLocaleString('en-US')} {String(p.currency || 'USD')}
                </p>
                <p className="text-xs text-muted-foreground">
                  Expiry: {p.expiry ? new Date(String(p.expiry)).toLocaleDateString() : '—'}
                </p>
              </div>
            ))}
            {payments.length === 0 && (
              <p className="text-sm text-muted-foreground">No payments yet.</p>
            )}
          </div>
          {paymentPagination.pages > 1 && (
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                disabled={paymentsPage <= 1}
                onClick={() => setPaymentsPage((p) => p - 1)}
              >
                Prev
              </Button>
              <span className="text-xs text-muted-foreground">
                {paymentsPage}/{paymentPagination.pages}
              </span>
              <Button
                size="sm"
                variant="outline"
                disabled={paymentsPage >= paymentPagination.pages}
                onClick={() => setPaymentsPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

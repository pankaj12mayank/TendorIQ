'use client';

import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Check, CreditCard, Loader2, Sparkles } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useBillingApi } from '@/hooks/use-billing';
import { useDemoStatus } from '@/hooks/use-demo-quota';
import { useSubscriptionAccess } from '@/hooks/use-subscription-access';
import { useCurrentUser } from '@/hooks/use-auth';
import {
  createRazorpayOrder,
  fetchPaymentConfig,
  openRazorpayCheckout,
} from '@/lib/razorpay-checkout';

type BillingInterval = 'monthly' | 'yearly';

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
  const { plans, currentSubscription, initialize, isLoading, fetchSubscription, fetchQuotaStatus } =
    useBillingApi();
  const { data: demoStatus, refetch: refetchDemo } = useDemoStatus();
  const { data: access, refetch: refetchAccess } = useSubscriptionAccess();
  const [interval, setInterval] = useState<BillingInterval>('monthly');
  const [payingPlanId, setPayingPlanId] = useState<string | null>(null);
  const [razorpayReady, setRazorpayReady] = useState<boolean | null>(null);

  useEffect(() => {
    void initialize();
    void fetchPaymentConfig().then((c) => setRazorpayReady(c.razorpay_enabled));
  }, [initialize]);

  useEffect(() => {
    if (searchParams.get('success') === 'true') {
      toast.success('Payment successful');
    }
  }, [searchParams]);

  const handleUpgrade = useCallback(
    async (plan: PlanCard) => {
      if (plan.isDemo) {
        toast.message('You are on the free demo plan');
        return;
      }
      setPayingPlanId(plan.id);
      try {
        const config = await fetchPaymentConfig();
        if (!config.razorpay_enabled) {
          toast.error('Razorpay not configured. Add keys to .env and restart API.');
          return;
        }
        const order = await createRazorpayOrder(plan.id, interval);
        await openRazorpayCheckout(order, {
          name: user?.name,
          email: user?.email,
          onSuccess: async () => {
            toast.success('Plan upgraded!');
            await fetchSubscription();
            await fetchQuotaStatus();
            await refetchDemo();
            await refetchAccess();
          },
        });
      } catch (err) {
        toast.error(err instanceof Error ? err.message : 'Payment failed');
      } finally {
        setPayingPlanId(null);
      }
    },
    [interval, user, fetchSubscription, fetchQuotaStatus, refetchDemo, refetchAccess]
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

      {demoStatus && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Sparkles className="h-5 w-5" />
              Demo usage — {demoStatus.plan} plan
            </CardTitle>
            <CardDescription>Resets monthly. Upgrade for higher limits.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 sm:grid-cols-2">
              {demoStatus.usage.map((row) => (
                <div
                  key={row.featureKey}
                  className={`rounded-lg border p-3 text-sm ${row.isExceeded ? 'border-destructive bg-destructive/5' : ''}`}
                >
                  <div className="font-medium capitalize">
                    {row.featureKey.replace(/_/g, ' ')}
                  </div>
                  <div className="text-muted-foreground">
                    {row.used} / {row.limit ?? '∞'} used
                    {row.remaining != null && ` · ${row.remaining} left`}
                  </div>
                </div>
              ))}
            </div>
            <p className="text-xs text-muted-foreground mt-3">
              AI tokens: {demoStatus.ai_tokens.used}
              {demoStatus.ai_tokens.limit != null && ` / ${demoStatus.ai_tokens.limit}`}
            </p>
          </CardContent>
        </Card>
      )}

      {currentSubscription && (
        <p className="text-sm">
          Current plan: <strong>{currentSubscription.plan}</strong> ({currentSubscription.status})
        </p>
      )}

      <div className="flex gap-2">
        <Button
          variant={interval === 'monthly' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setInterval('monthly')}
        >
          Monthly
        </Button>
        <Button
          variant={interval === 'yearly' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setInterval('yearly')}
        >
          Yearly
        </Button>
      </div>

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
                    {plan.isDemo ? 'Free' : `₹${price.toLocaleString('en-IN')}`}
                    {!plan.isDemo && (
                      <span className="text-sm font-normal text-muted-foreground">
                        /{interval === 'yearly' ? 'yr' : 'mo'}
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
                    variant={plan.isDemo ? 'outline' : 'default'}
                    disabled={isCurrent || payingPlanId === plan.id}
                    onClick={() => void handleUpgrade(plan)}
                  >
                    {payingPlanId === plan.id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : plan.isDemo ? (
                      'Current demo'
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
    </div>
  );
}

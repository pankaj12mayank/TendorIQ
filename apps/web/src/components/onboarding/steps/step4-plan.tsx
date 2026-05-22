'use client';

import { useState, useEffect } from 'react';
import { normalizeBillingCycle } from '@/lib/billing-plan-bridge';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { useOnboardingApi, Step4Data } from '@/hooks/use-onboarding';
import type { Plan } from '@/types/onboarding';
import { useOnboardingStore } from '@/stores/onboarding-store';
import { AlertCircle, CreditCard, Loader2, ArrowLeft, Check, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

export function Step4Plan() {
  const router = useRouter();
  const store = useOnboardingStore();
  const { submitStep4, fetchPlans, loading, error } = useOnboardingApi();

  const [plans, setPlans] = useState<Plan[]>([]);
  const [plansLoading, setPlansLoading] = useState(true);

  const [selectedPlan, setSelectedPlan] = useState<string>(
    (store.step4Data.plan_id as string) || 'professional'
  );
  const [billingCycle, setBillingCycle] = useState<string>(
    normalizeBillingCycle((store.step4Data.billing_cycle as string) || 'monthly')
  );

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const loaded = await fetchPlans();
        if (!cancelled && loaded.length > 0) {
          setPlans(loaded);
          if (!loaded.some((p) => p.id === selectedPlan)) {
            const fallback = loaded.find((p) => p.recommended)?.id ?? loaded[0].id;
            setSelectedPlan(fallback);
          }
        }
      } finally {
        if (!cancelled) setPlansLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [fetchPlans, selectedPlan]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const data: Step4Data = {
        plan_id: selectedPlan,
        billing_cycle: billingCycle,
      };
      const res = await submitStep4(data);
      if (res.success) {
        store.setCurrentStep(5);
      }
    } catch {
      // Error handled by hook
    }
  };

  const handleBack = () => {
    store.setCurrentStep(3);
    router.push('/onboarding');
  };

  const getPrice = (plan: Plan) => {
    return billingCycle === 'yearly' ? plan.price_yearly : plan.price_monthly;
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center gap-2">
          <CreditCard className="h-6 w-6 text-primary" />
          <CardTitle>Choose Your Plan</CardTitle>
        </div>
        <CardDescription>
          Select the plan that best fits your needs. You can upgrade or downgrade at any time.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="flex items-center gap-2 rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
              <AlertCircle className="h-4 w-4" />
              {error}
            </div>
          )}

          <div className="flex items-center justify-center gap-4">
            <label className={cn(
              'flex cursor-pointer items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-colors',
              billingCycle === 'monthly'
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted hover:bg-muted/80'
            )}>
              <input
                type="radio"
                name="billing"
                value="monthly"
                checked={billingCycle === 'monthly'}
                onChange={() => setBillingCycle('monthly')}
                className="sr-only"
              />
              Monthly
            </label>
            <label className={cn(
              'flex cursor-pointer items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-colors',
              billingCycle === 'yearly'
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted hover:bg-muted/80'
            )}>
              <input
                type="radio"
                name="billing"
                value="yearly"
                checked={billingCycle === 'yearly'}
                onChange={() => setBillingCycle('yearly')}
                className="sr-only"
              />
              Yearly
              <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700 dark:bg-green-900 dark:text-green-300">
                Save 20%
              </span>
            </label>
          </div>

          {plansLoading && plans.length === 0 && (
            <div className="flex justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          )}

          <div className="grid gap-4 sm:grid-cols-2">
            {plans.map((plan) => {
              const price = getPrice(plan);
              const isSelected = selectedPlan === plan.id;

              return (
                <button
                  key={plan.id}
                  type="button"
                  onClick={() => setSelectedPlan(plan.id)}
                  className={cn(
                    'relative flex flex-col rounded-lg border-2 p-4 text-left transition-all',
                    isSelected
                      ? 'border-primary bg-primary/5'
                      : 'border-input hover:border-primary/50 hover:bg-muted/50'
                  )}
                >
                  {plan.recommended && (
                    <div className="absolute -top-3 right-4 flex items-center gap-1 rounded-full bg-primary px-3 py-1 text-xs font-medium text-primary-foreground">
                      <Sparkles className="h-3 w-3" />
                      Recommended
                    </div>
                  )}
                  {isSelected && (
                    <div className="absolute right-4 top-4 flex h-5 w-5 items-center justify-center rounded-full bg-primary">
                      <Check className="h-3 w-3 text-primary-foreground" />
                    </div>
                  )}

                  <div className="mb-2">
                    <h3 className="text-lg font-bold">{plan.name}</h3>
                    <p className="mt-1 text-sm text-muted-foreground">{plan.description}</p>
                  </div>

                  <div className="mb-4">
                    <span className="text-3xl font-bold">
                      ${price === 0 ? '0' : price.toLocaleString()}
                    </span>
                    <span className="text-muted-foreground">
                      /{billingCycle === 'yearly' ? 'year' : 'month'}
                    </span>
                  </div>

                  <ul className="space-y-2 text-sm">
                    {plan.features.map((feature) => (
                      <li key={feature.name} className="flex items-center gap-2">
                        {feature.included ? (
                          <Check className="h-4 w-4 text-green-500" />
                        ) : (
                          <span className="h-4 w-4 rounded-full border border-muted-foreground/30" />
                        )}
                        <span className={feature.included ? '' : 'text-muted-foreground'}>
                          {feature.name}
                          {feature.limit && (
                            <span className="ml-1 text-xs text-muted-foreground">({feature.limit})</span>
                          )}
                        </span>
                      </li>
                    ))}
                  </ul>
                </button>
              );
            })}
          </div>

          <div className="flex justify-between gap-3 pt-4">
            <Button type="button" variant="outline" onClick={handleBack} disabled={loading}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
            <Button type="submit" disabled={loading || plansLoading || plans.length === 0}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Continue with {plans.find((p) => p.id === selectedPlan)?.name ?? 'plan'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
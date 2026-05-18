'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import {
  Check,
  X,
  Zap,
  Star,
  Crown,
  CreditCard,
  ArrowRight,
  Sparkles,
  TrendingUp,
  AlertCircle,
  Clock,
  Download,
} from 'lucide-react';
import { Plan, BillingInterval } from '../types';
import { PLANS, PLAN_COLORS, formatCurrency, getDaysRemaining } from '../constants';
import { useBillingStore } from '../store';
import { cn } from '@/lib/utils';

interface PlanComparisonProps {
  currentPlanId?: string;
  onSelectPlan?: (planId: string, interval: BillingInterval) => void;
  showUpgradeOnly?: boolean;
}

export function PlanComparison({ 
  currentPlanId, 
  onSelectPlan,
  showUpgradeOnly = false 
}: PlanComparisonProps) {
  const [selectedInterval, setSelectedInterval] = useState<BillingInterval>('monthly');
  const { currentSubscription, isProcessing } = useBillingStore();

  const availablePlans = PLANS.filter(p => p.isActive);
  
  const handleSelectPlan = (plan: Plan) => {
    if (onSelectPlan) {
      onSelectPlan(plan.id, selectedInterval);
    }
  };

  const isCurrentPlan = (planId: string) => currentPlanId === planId || currentSubscription?.planId === planId;

  const getPlanIcon = (planName: string) => {
    switch (planName) {
      case 'free':
        return <Zap className="w-6 h-6" />;
      case 'pro':
        return <Sparkles className="w-6 h-6" />;
      case 'enterprise':
        return <Crown className="w-6 h-6" />;
      default:
        return <Star className="w-6 h-6" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Choose Your Plan</h2>
          <p className="text-muted-foreground">Select the plan that fits your needs</p>
        </div>
        
        <div className="flex items-center gap-2 p-1 bg-muted rounded-lg">
          <button
            onClick={() => setSelectedInterval('monthly')}
            className={cn(
              'px-4 py-2 rounded-md text-sm font-medium transition-colors',
              selectedInterval === 'monthly'
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            Monthly
          </button>
          <button
            onClick={() => setSelectedInterval('annual')}
            className={cn(
              'px-4 py-2 rounded-md text-sm font-medium transition-colors',
              selectedInterval === 'annual'
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            Annual
            <Badge variant="secondary" className="ml-2 text-xs">Save 20%</Badge>
          </button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {availablePlans.map((plan) => {
          const price = selectedInterval === 'monthly' ? plan.priceMonthly : plan.priceAnnual;
          const isCurrent = isCurrentPlan(plan.id);
          const isPopular = plan.name === 'pro';
          const savings = selectedInterval === 'annual' 
            ? Math.round((plan.priceMonthly * 12 - plan.priceAnnual) / 100) 
            : 0;

          return (
            <Card
              key={plan.id}
              className={cn(
                'relative transition-all',
                isCurrent && 'border-primary ring-2 ring-primary/20',
                isPopular && 'border-blue-500'
              )}
            >
              {isPopular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <Badge className="bg-blue-500 text-white">Most Popular</Badge>
                </div>
              )}

              {isCurrent && (
                <div className="absolute top-4 right-4">
                  <Badge className="bg-primary text-primary-foreground">Current Plan</Badge>
                </div>
              )}

              <CardHeader className="pb-4">
                <div className={cn('w-12 h-12 rounded-lg flex items-center justify-center mb-4', PLAN_COLORS[plan.name as keyof typeof PLAN_COLORS])}>
                  {getPlanIcon(plan.name)}
                </div>
                <CardTitle className="text-xl">{plan.displayName}</CardTitle>
                <CardDescription>{plan.description}</CardDescription>
              </CardHeader>

              <CardContent className="space-y-4">
                <div className="text-center py-4">
                  <div className="flex items-baseline justify-center gap-1">
                    <span className="text-4xl font-bold">{formatCurrency(price)}</span>
                    {price > 0 && <span className="text-muted-foreground">/{selectedInterval === 'monthly' ? 'mo' : 'yr'}</span>}
                  </div>
                  {savings > 0 && (
                    <p className="text-sm text-green-600 mt-1">Save ${savings}/year</p>
                  )}
                  {plan.trialDays > 0 && !isCurrent && (
                    <p className="text-sm text-muted-foreground mt-1">{plan.trialDays} day free trial</p>
                  )}
                </div>

                <Separator />

                <ul className="space-y-3">
                  {plan.features.slice(0, 8).map((feature, idx) => (
                    <li key={idx} className="flex items-start gap-3">
                      {feature.isEnabled ? (
                        <Check className="w-5 h-5 text-green-600 flex-shrink-0" />
                      ) : (
                        <X className="w-5 h-5 text-gray-300 flex-shrink-0" />
                      )}
                      <span className={cn('text-sm', !feature.isEnabled && 'text-muted-foreground')}>
                        {feature.limit === null && feature.isEnabled
                          ? feature.name
                          : feature.limit !== null
                          ? `${feature.limit} ${feature.unit} ${feature.name}`
                          : null}
                        {!feature.isEnabled && <span className="text-xs ml-1">(Upgrade required)</span>}
                      </span>
                    </li>
                  ))}
                </ul>

                <Separator />

                <Button
                  className="w-full"
                  variant={isCurrent ? 'outline' : isPopular ? 'default' : 'outline'}
                  disabled={isCurrent || isProcessing}
                  onClick={() => handleSelectPlan(plan)}
                >
                  {isCurrent ? (
                    'Current Plan'
                  ) : (
                    <>
                      {plan.name === 'enterprise' ? (
                        <>
                          <Crown className="w-4 h-4 mr-2" />
                          Contact Sales
                        </>
                      ) : (
                        <>
                          Get Started
                          <ArrowRight className="w-4 h-4 ml-2" />
                        </>
                      )}
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

interface QuotaUsageCardProps {
  className?: string;
}

export function QuotaUsageCard({ className }: QuotaUsageCardProps) {
  const { quotaStatus, isLoading } = useBillingStore();

  return (
    <Card className={cn(className)}>
      <CardHeader>
        <CardTitle>Usage This Period</CardTitle>
        <CardDescription>Your current usage against plan limits</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {quotaStatus.map((quota) => {
            const percentage = quota.limit ? (quota.used / quota.limit) * 100 : 0;
            const isWarning = percentage >= 80;
            const isExceeded = percentage >= 100;

            return (
              <div key={quota.featureKey} className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{quota.featureName}</span>
                  <span className={cn(
                    'text-sm',
                    isExceeded && 'text-red-600 font-medium',
                    isWarning && !isExceeded && 'text-yellow-600',
                    !isWarning && !isExceeded && 'text-muted-foreground'
                  )}>
                    {quota.used} / {quota.isUnlimited ? '∞' : quota.limit}
                  </span>
                </div>
                <div className="relative h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className={cn(
                      'h-full rounded-full transition-all',
                      isExceeded && 'bg-red-500',
                      isWarning && !isExceeded && 'bg-yellow-500',
                      !isWarning && !isExceeded && 'bg-blue-500'
                    )}
                    style={{ width: `${Math.min(percentage, 100)}%` }}
                  />
                </div>
                {quota.isUnlimited ? (
                  <p className="text-xs text-green-600">Unlimited</p>
                ) : quota.remaining !== null ? (
                  <p className="text-xs text-muted-foreground">
                    {quota.remaining} remaining
                  </p>
                ) : null}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

interface SubscriptionStatusCardProps {
  className?: string;
}

export function SubscriptionStatusCard({ className }: SubscriptionStatusCardProps) {
  const { currentSubscription, isProcessing, cancelSubscription, reactivateSubscription } = useBillingStore();

  if (!currentSubscription) {
    return (
      <Card className={cn(className)}>
        <CardContent className="py-8">
          <div className="text-center">
            <AlertCircle className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No Active Subscription</h3>
            <p className="text-muted-foreground mb-4">Subscribe to a plan to unlock more features</p>
            <Button>View Plans</Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  const daysRemaining = getDaysRemaining(currentSubscription.currentPeriodEnd);
  const isCanceled = currentSubscription.status === 'canceled';

  return (
    <Card className={cn(className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={cn('w-12 h-12 rounded-lg flex items-center justify-center', PLAN_COLORS[currentSubscription.plan?.name as keyof typeof PLAN_COLORS])}>
              <Star className="w-6 h-6" />
            </div>
            <div>
              <CardTitle>{currentSubscription.plan?.displayName} Plan</CardTitle>
              <CardDescription>
                {currentSubscription.billingInterval === 'monthly' ? 'Monthly' : 'Annual'} billing
              </CardDescription>
            </div>
          </div>
          <Badge className={cn(
            currentSubscription.status === 'active' && 'bg-green-100 text-green-800',
            currentSubscription.status === 'canceled' && 'bg-red-100 text-red-800',
            currentSubscription.status === 'past_due' && 'bg-yellow-100 text-yellow-800'
          )}>
            {currentSubscription.status}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {isCanceled ? (
          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-center gap-2 text-yellow-800">
              <AlertCircle className="w-5 h-5" />
              <span className="font-medium">Subscription will end on {new Date(currentSubscription.currentPeriodEnd).toLocaleDateString()}</span>
            </div>
            <p className="text-sm text-yellow-700 mt-2">
              Your subscription has been canceled. You can reactivate it anytime before the period ends.
            </p>
            <Button 
              className="mt-3" 
              onClick={() => reactivateSubscription()}
              disabled={isProcessing}
            >
              {isProcessing ? 'Processing...' : 'Reactivate Subscription'}
            </Button>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
              <div>
                <p className="text-sm text-muted-foreground">Next billing date</p>
                <p className="text-lg font-semibold">
                  {new Date(currentSubscription.currentPeriodEnd).toLocaleDateString()}
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-muted-foreground">Days remaining</p>
                <p className={cn(
                  'text-lg font-semibold',
                  daysRemaining <= 3 && 'text-red-600',
                  daysRemaining <= 7 && daysRemaining > 3 && 'text-yellow-600'
                )}>
                  {daysRemaining} days
                </p>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">
                {currentSubscription.billingInterval === 'monthly' 
                  ? formatCurrency(currentSubscription.plan?.priceMonthly || 0)
                  : formatCurrency(currentSubscription.plan?.priceAnnual || 0)} / {currentSubscription.billingInterval === 'monthly' ? 'month' : 'year'}
              </span>
              <div className="flex gap-2">
                <Button variant="outline" size="sm">
                  Change Plan
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  className="text-red-600 hover:text-red-700"
                  onClick={() => cancelSubscription()}
                  disabled={isProcessing}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

export default PlanComparison;
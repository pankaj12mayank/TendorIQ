'use client';

/** Platform-wide billing overview (super admin) — not tenant `/dashboard/billing`. */
import React, { useState, useEffect } from 'react';
import { useBillingApi } from '@/hooks/use-admin';
import { LoadingState } from '@/components/ui/loading-state';
import { ErrorState } from '@/components/ui/error-state';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import {
  CreditCard,
  DollarSign,
  Download,
  Calendar,
  CheckCircle,
  AlertCircle,
  Clock,
  TrendingUp,
  Zap,
} from 'lucide-react';
import { BillingPlan, Subscription } from '../types';
import { cn } from '@/lib/utils';

const STATUS_COLORS: Record<string, string> = {
  paid: 'bg-green-100 text-green-800',
  pending: 'bg-yellow-100 text-yellow-800',
  failed: 'bg-red-100 text-red-800',
  refunded: 'bg-gray-100 text-gray-800',
};

export function Billing() {
  const { plans, subscriptions, isLoading, error, fetchBilling } = useBillingApi();
  const [selectedPlan, setSelectedPlan] = useState<string>('professional');

  useEffect(() => {
    void fetchBilling();
  }, [fetchBilling]);

  if (isLoading && plans.length === 0) {
    return <LoadingState message="Loading billing..." />;
  }

  if (error) {
    return <ErrorState title="Billing unavailable" message={error} onRetry={() => void fetchBilling()} />;
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const currentSubscription = (subscriptions[0] as Subscription | undefined) ?? {
    id: 'none',
    userId: '',
    planId: 'starter',
    status: 'active',
    currentPeriodStart: new Date().toISOString(),
    currentPeriodEnd: new Date().toISOString(),
    cancelAtPeriodEnd: false,
  };
  const currentPlan = plans.find((p) => p.id === currentSubscription.planId) ?? plans[0];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Billing & Subscription</h2>
          <p className="text-muted-foreground">Manage your subscription and invoices</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Current Plan</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between p-6 bg-primary/5 rounded-lg mb-6">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="text-2xl font-bold">{currentPlan?.name}</h3>
                  <Badge className="bg-green-100 text-green-800">Active</Badge>
                </div>
                <p className="text-muted-foreground">
                  ${currentPlan?.price}/{currentPlan?.interval === 'monthly' ? 'mo' : 'year'}
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-muted-foreground">Next billing date</p>
                <p className="font-semibold">{formatDate(currentSubscription.currentPeriodEnd)}</p>
              </div>
            </div>

            <h4 className="font-medium mb-4">Plan Limits</h4>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Users</span>
                  <span>{currentPlan?.limits.users === -1 ? 'Unlimited' : `${currentPlan?.limits.users}/20`}</span>
                </div>
                <Progress value={65} />
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Documents</span>
                  <span>{currentPlan?.limits.documents === -1 ? 'Unlimited' : `124/500`}</span>
                </div>
                <Progress value={25} />
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">API Calls</span>
                  <span>8,234/10,000</span>
                </div>
                <Progress value={82} />
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Storage</span>
                  <span>2.4GB/10GB</span>
                </div>
                <Progress value={24} />
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-base">Quick Stats</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm">Total Spent</span>
                </div>
                <span className="font-semibold">$8,964</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm">This Month</span>
                </div>
                <span className="font-semibold">$299</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm">vs Last Month</span>
                </div>
                <span className="text-green-600 font-semibold">+5%</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Payment Method</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-3 p-3 border rounded-lg">
                <CreditCard className="w-5 h-5 text-muted-foreground" />
                <div className="flex-1">
                  <p className="font-medium">Visa ending in 4242</p>
                  <p className="text-sm text-muted-foreground">Expires 12/2027</p>
                </div>
                <Badge>Default</Badge>
              </div>
              <Button variant="outline" className="w-full mt-4">
                Update Payment Method
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>

      <Tabs defaultValue="plans">
        <TabsList>
          <TabsTrigger value="plans">Available Plans</TabsTrigger>
          <TabsTrigger value="invoices">Invoices</TabsTrigger>
        </TabsList>

        <TabsContent value="plans">
          <Card>
            <CardHeader>
              <CardTitle>Available Plans</CardTitle>
              <CardDescription>Choose the plan that fits your needs</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                {plans.map((plan) => (
                  <div
                    key={plan.id}
                    className={cn(
                      'p-6 border rounded-lg cursor-pointer transition-all',
                      selectedPlan === plan.id
                        ? 'border-primary bg-primary/5 ring-2 ring-primary'
                        : 'hover:border-primary/50'
                    )}
                    onClick={() => setSelectedPlan(plan.id)}
                  >
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-bold">{plan.name}</h3>
                      {plan.id === currentSubscription.planId && (
                        <Badge className="bg-primary text-primary-foreground">Current</Badge>
                      )}
                    </div>
                    <div className="mb-4">
                      <span className="text-3xl font-bold">${plan.price}</span>
                      <span className="text-muted-foreground">/{plan.interval === 'monthly' ? 'mo' : 'year'}</span>
                    </div>
                    <ul className="space-y-2 mb-6">
                      {plan.features.map((feature, idx) => (
                        <li key={idx} className="flex items-center gap-2 text-sm">
                          <CheckCircle className="w-4 h-4 text-green-600" />
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>
                    <Button
                      variant={selectedPlan === plan.id ? 'default' : 'outline'}
                      className="w-full"
                      disabled={plan.id === currentSubscription.planId}
                    >
                      {plan.id === currentSubscription.planId ? 'Current Plan' : 'Select Plan'}
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="invoices">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Invoice History</CardTitle>
              <Button variant="outline" size="sm">
                <Download className="w-4 h-4 mr-2" />
                Download All
              </Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[].map((invoice: { id: string; description: string; amount: number; status: string; createdAt: string }) => (
                  <div key={invoice.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-4">
                      <div className={cn(
                        'w-10 h-10 rounded-full flex items-center justify-center',
                        invoice.status === 'paid' ? 'bg-green-100' : 'bg-yellow-100'
                      )}>
                        {invoice.status === 'paid' ? (
                          <CheckCircle className="w-5 h-5 text-green-600" />
                        ) : (
                          <Clock className="w-5 h-5 text-yellow-600" />
                        )}
                      </div>
                      <div>
                        <p className="font-medium">{invoice.description}</p>
                        <p className="text-sm text-muted-foreground">
                          {formatDate(invoice.createdAt)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-lg font-semibold">${invoice.amount}</span>
                      <Badge className={STATUS_COLORS[invoice.status as keyof typeof STATUS_COLORS] || 'bg-gray-100'}>
                        {invoice.status}
                      </Badge>
                      <Button variant="ghost" size="sm">
                        <Download className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default Billing;
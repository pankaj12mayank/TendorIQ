'use client';

import React, { useEffect, useState } from 'react';
import { useBillingStore } from '@/components/billing/store';
import { useBillingApi, useQuotaEnforcement } from '@/hooks/use-billing';
import { 
  PlanComparison, 
  QuotaUsageCard, 
  SubscriptionStatusCard,
  BillingHistory,
  PaymentMethodsCard,
  UpcomingBillingCard
} from '@/components/billing';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import {
  CreditCard,
  Receipt,
  Settings,
  BarChart3,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';
import { cn } from '@/lib/utils';

export default function BillingPage() {
  const [activeTab, setActiveTab] = useState('plans');
  const { currentSubscription, isProcessing } = useBillingStore();
  const {
    isLoading,
    changePlan,
    cancelSubscription: apiCancelSubscription,
    initialize,
  } = useBillingApi();
  const { getAllQuotaStatus, getUpgradePrompt } = useQuotaEnforcement();

  useEffect(() => {
    void initialize();
  }, [initialize]);

  const quotaStatus = getAllQuotaStatus();
  const warningQuotas = quotaStatus.filter(q => 
    !q.isUnlimited && q.remaining !== null && q.remaining <= 10
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Billing & Subscription</h1>
          <p className="text-muted-foreground">Manage your subscription and billing</p>
        </div>
        <Button variant="outline">
          <ExternalLink className="w-4 h-4 mr-2" />
          Open Billing Portal
        </Button>
      </div>

      {warningQuotas.length > 0 && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-yellow-600" />
              <div className="flex-1">
                <p className="font-medium text-yellow-800">Usage Warning</p>
                <p className="text-sm text-yellow-700">
                  You're running low on: {warningQuotas.map(q => q.featureName).join(', ')}
                </p>
              </div>
              <Button size="sm" onClick={() => setActiveTab('plans')}>
                Upgrade Plan
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="plans">
                <CreditCard className="w-4 h-4 mr-2" />
                Plans
              </TabsTrigger>
              <TabsTrigger value="usage">
                <BarChart3 className="w-4 h-4 mr-2" />
                Usage
              </TabsTrigger>
              <TabsTrigger value="invoices">
                <Receipt className="w-4 h-4 mr-2" />
                Invoices
              </TabsTrigger>
              <TabsTrigger value="payment">
                <Settings className="w-4 h-4 mr-2" />
                Payment
              </TabsTrigger>
            </TabsList>

            <TabsContent value="plans" className="space-y-6">
              <PlanComparison 
                currentPlanId={currentSubscription?.planId}
                onSelectPlan={async (planId, interval) => {
                  await changePlan(planId, interval);
                }}
              />
            </TabsContent>

            <TabsContent value="usage" className="space-y-6">
              <div className="grid gap-6 md:grid-cols-2">
                <QuotaUsageCard />
                
                <Card>
                  <CardHeader>
                    <CardTitle>Usage Recommendations</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {quotaStatus.map((quota) => {
                      const prompt = getUpgradePrompt(quota.featureKey);
                      if (!prompt) return null;

                      return (
                        <div key={quota.featureKey} className="p-3 border rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium">{quota.featureName}</span>
                            <Badge variant="outline">
                              {quota.remaining} remaining
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground mb-3">{prompt}</p>
                          <Button size="sm" variant="outline" onClick={() => setActiveTab('plans')}>
                            Upgrade
                          </Button>
                        </div>
                      );
                    })}
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="invoices">
              <BillingHistory />
            </TabsContent>

            <TabsContent value="payment">
              <div className="grid gap-6 md:grid-cols-2">
                <PaymentMethodsCard />
                <UpcomingBillingCard />
              </div>
            </TabsContent>
          </Tabs>
        </div>

        <div className="space-y-6">
          <SubscriptionStatusCard />

          <Card>
            <CardHeader>
              <CardTitle>Quick Stats</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span className="text-sm">Total Paid</span>
                </div>
                <span className="font-semibold">$24,500</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                <div className="flex items-center gap-3">
                  <Receipt className="w-5 h-5 text-blue-600" />
                  <span className="text-sm">Invoices</span>
                </div>
                <span className="font-semibold">5</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                <div className="flex items-center gap-3">
                  <CreditCard className="w-5 h-5 text-purple-600" />
                  <span className="text-sm">Next Payment</span>
                </div>
                <span className="font-semibold">$49.00</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Need Help?</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button variant="outline" className="w-full justify-start">
                View FAQ
              </Button>
              <Button variant="outline" className="w-full justify-start">
                Contact Support
              </Button>
              <Button variant="outline" className="w-full justify-start">
                Talk to Sales
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
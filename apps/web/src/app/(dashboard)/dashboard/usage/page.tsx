'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useUsageStore } from '@/components/usage/store';
import { useUsageApi, useQuotaEnforcement } from '@/components/usage/hooks/use-usage';
import { useObservability } from '@/hooks/use-observability';
import { 
  AlertPanel, 
  UsageWidget, 
  UsageDetailCard, 
  UsageBreakdown,
  AdminOverridePanel,
  RealtimeAlertToast,
} from '@/components/usage';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  BarChart3,
  AlertTriangle,
  Shield,
  RefreshCw,
  Activity,
  TrendingUp,
  Zap,
  Clock,
} from 'lucide-react';
import { FeatureKey, QuotaStatus } from '@/components/usage/types';
import { FEATURE_CONFIG, FEATURE_CATEGORIES, getAlertLevel } from '@/components/usage/constants';
import { cn } from '@/lib/utils';

export default function UsagePage() {
  const store = useUsageStore();
  const { quotas, alerts, usageSummary, isLoading, fetchQuotas, fetchAlerts, fetchUsageSummary, subscribeToRealtime, getUsageByCategory } = useUsageApi();
  const { summary: opsSummary, fetchSummary: fetchOpsSummary } = useObservability();
  const [showUpgradePrompt, setShowUpgradePrompt] = useState<string | null>(null);

  useEffect(() => {
    fetchQuotas();
    fetchAlerts();
    fetchUsageSummary();
    void fetchOpsSummary().catch(() => {});

    const unsubscribe = subscribeToRealtime();
    return () => unsubscribe();
  }, [fetchQuotas, fetchAlerts, fetchUsageSummary, fetchOpsSummary, subscribeToRealtime]);

  const categories = getUsageByCategory();
  const activeAlerts = alerts.filter(a => !a.isDismissed);
  const criticalAlerts = activeAlerts.filter(a => a.alertType === 'critical' || a.alertType === 'exceeded');

  const totalUsed = quotas.reduce((sum, q) => sum + q.used, 0);
  const totalLimit = quotas.reduce((sum, q) => sum + (q.limit || 0), 0);
  const avgPercentage = totalLimit > 0 ? (totalUsed / totalLimit) * 100 : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Usage & Quotas</h1>
          <p className="text-muted-foreground">Monitor your resource usage and quotas</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs">
            <span className="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse" />
            Real-time tracking
          </Badge>
          <Button variant="outline" onClick={() => {
            fetchQuotas();
            fetchAlerts();
            fetchUsageSummary();
            void fetchOpsSummary();
          }}>
            <RefreshCw className={cn('w-4 h-4 mr-2', isLoading && 'animate-spin')} />
            Refresh
          </Button>
        </div>
      </div>

      {criticalAlerts.length > 0 && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600" />
              <div className="flex-1">
                <p className="font-medium text-red-800">Critical Quota Alert</p>
                <p className="text-sm text-red-700">
                  {criticalAlerts.length} feature(s) approaching or exceeding limits
                </p>
              </div>
              <Button size="sm" asChild>
                <Link href="/dashboard/billing">Upgrade Plan</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-4">
        <Card className="lg:col-span-3">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Quick Stats</CardTitle>
              <Activity className="w-5 h-5 text-muted-foreground" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <p className="text-3xl font-bold text-blue-600">{quotas.length}</p>
                <p className="text-sm text-muted-foreground">Tracked Features</p>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <p className="text-3xl font-bold text-green-600">{avgPercentage.toFixed(0)}%</p>
                <p className="text-sm text-muted-foreground">Avg Usage</p>
              </div>
              <div className="text-center p-4 bg-yellow-50 rounded-lg">
                <p className="text-3xl font-bold text-yellow-600">{activeAlerts.length}</p>
                <p className="text-sm text-muted-foreground">Active Alerts</p>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <p className="text-3xl font-bold text-purple-600">{totalUsed.toLocaleString()}</p>
                <p className="text-sm text-muted-foreground">Total Used</p>
              </div>
            </div>
            {opsSummary && (
              <p className="mt-4 text-sm text-muted-foreground">
                Operations: {opsSummary.queue.active_jobs} active jobs ·{' '}
                {opsSummary.queue.failure_rate}% queue failures ·{' '}
                {opsSummary.ai.total_tokens.toLocaleString()} AI tokens ·{' '}
                {opsSummary.processing.documents_processed} docs processed (24h)
              </p>
            )}
          </CardContent>
        </Card>

        <div className="space-y-4">
          <AlertPanel />
        </div>
      </div>

      <Tabs defaultValue="overview">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">
            <BarChart3 className="w-4 h-4 mr-2" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="categories">
            <Zap className="w-4 h-4 mr-2" />
            Categories
          </TabsTrigger>
          <TabsTrigger value="breakdown">
            <TrendingUp className="w-4 h-4 mr-2" />
            Breakdown
          </TabsTrigger>
          <TabsTrigger value="admin">
            <Shield className="w-4 h-4 mr-2" />
            Admin
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <UsageWidget />
          
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {quotas.map((quota) => (
              <UsageDetailCard key={quota.featureKey} quota={quota} />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="categories" className="space-y-6">
          {Object.entries(categories).map(([category, categoryQuotas]) => (
            <Card key={category}>
              <CardHeader>
                <CardTitle>{category}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {categoryQuotas.map((quota) => (
                    <div key={quota.featureKey} className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium">{quota.featureName}</span>
                        <Badge variant="outline" className="text-xs">
                          {quota.percentage.toFixed(0)}%
                        </Badge>
                      </div>
                      <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className={cn(
                            'h-full rounded-full',
                            getAlertLevel(quota.percentage) === 'exceeded' && 'bg-red-500',
                            getAlertLevel(quota.percentage) === 'critical' && 'bg-orange-500',
                            getAlertLevel(quota.percentage) === 'warning' && 'bg-yellow-500',
                            getAlertLevel(quota.percentage) === 'none' && 'bg-green-500'
                          )}
                          style={{ width: `${Math.min(quota.percentage, 100)}%` }}
                        />
                      </div>
                      <p className="text-xs text-muted-foreground mt-2">
                        {quota.used} / {quota.isUnlimited ? '∞' : quota.limit} {FEATURE_CONFIG[quota.featureKey]?.unit}
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="breakdown">
          <UsageBreakdown />
        </TabsContent>

        <TabsContent value="admin">
          <div className="grid gap-6 lg:grid-cols-2">
            <AdminOverridePanel />
            <Card>
              <CardHeader>
                <CardTitle>Admin Tools</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium mb-3">Quick Actions</h4>
                  <div className="space-y-2">
                    <Button variant="outline" className="w-full justify-start">
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Reset All Quotas
                    </Button>
                    <Button variant="outline" className="w-full justify-start">
                      <Activity className="w-4 h-4 mr-2" />
                      Export Usage Report
                    </Button>
                    <Button variant="outline" className="w-full justify-start">
                      <Clock className="w-4 h-4 mr-2" />
                      View Usage History
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {showUpgradePrompt && (
        <Card className="fixed bottom-4 right-4 max-w-sm shadow-lg z-50">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-yellow-600" />
              <div className="flex-1">
                <p className="font-medium">Upgrade Recommended</p>
                <p className="text-sm text-muted-foreground">
                  You've used {showUpgradePrompt}% of your quota
                </p>
              </div>
              <Button size="sm" asChild>
                <Link href="/dashboard/billing">Upgrade</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
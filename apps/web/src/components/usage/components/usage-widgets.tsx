'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Upload,
  HardDrive,
  Cpu,
  FileText,
  Download,
  Zap,
  File,
  Users,
  Briefcase,
  TrendingUp,
  Brain,
  Scan,
  RefreshCw,
  ChevronRight,
  TrendingDown,
  Minus,
} from 'lucide-react';
import { QuotaStatus, FeatureKey } from '../types';
import { useUsageStore } from '../store';
import { FEATURE_CONFIG, getAlertLevel } from '../constants';
import { cn } from '@/lib/utils';

const FEATURE_ICONS: Record<FeatureKey, React.ReactNode> = {
  uploads: <Upload className="w-5 h-5" />,
  storage: <HardDrive className="w-5 h-5" />,
  ai_tokens: <Cpu className="w-5 h-5" />,
  proposal_generations: <FileText className="w-5 h-5" />,
  exports: <Download className="w-5 h-5" />,
  api_requests: <Zap className="w-5 h-5" />,
  documents: <File className="w-5 h-5" />,
  users: <Users className="w-5 h-5" />,
  tenders: <Briefcase className="w-5 h-5" />,
  bids: <TrendingUp className="w-5 h-5" />,
  ai_analysis: <Brain className="w-5 h-5" />,
  ocr_pages: <Scan className="w-5 h-5" />,
};

interface UsageWidgetProps {
  className?: string;
}

export function UsageWidget({ className }: UsageWidgetProps) {
  const { quotas, isRealTimeActive, realtimeUpdates } = useUsageStore();

  return (
    <Card className={cn(className)}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="flex items-center gap-3">
          <CardTitle>Usage Overview</CardTitle>
          {isRealTimeActive && (
            <Badge variant="outline" className="text-xs bg-green-50 text-green-600 border-green-200">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse" />
              Live
            </Badge>
          )}
        </div>
        <Button variant="ghost" size="sm">
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {quotas.slice(0, 6).map((quota) => (
            <QuotaMiniCard key={quota.featureKey} quota={quota} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

interface QuotaMiniCardProps {
  quota: QuotaStatus;
}

export function QuotaMiniCard({ quota }: QuotaMiniCardProps) {
  const alertLevel = getAlertLevel(quota.percentage);

  return (
    <div className="p-4 border rounded-lg bg-card hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className={cn(
            'p-2 rounded-lg',
            alertLevel === 'exceeded' && 'bg-red-100 text-red-600',
            alertLevel === 'critical' && 'bg-orange-100 text-orange-600',
            alertLevel === 'warning' && 'bg-yellow-100 text-yellow-600',
            alertLevel === 'none' && 'bg-blue-100 text-blue-600'
          )}>
            {FEATURE_ICONS[quota.featureKey]}
          </div>
          <span className="font-medium text-sm">{quota.featureName}</span>
        </div>
        {alertLevel !== 'none' && (
          <Badge
            variant="outline"
            className={cn(
              'text-xs',
              alertLevel === 'exceeded' && 'border-red-300 text-red-600',
              alertLevel === 'critical' && 'border-orange-300 text-orange-600',
              alertLevel === 'warning' && 'border-yellow-300 text-yellow-600'
            )}
          >
            {alertLevel}
          </Badge>
        )}
      </div>

      <div className="mb-2">
        <div className="flex items-center justify-between text-sm mb-1">
          <span className="text-muted-foreground">
            {quota.used} / {quota.isUnlimited ? '∞' : quota.limit}
          </span>
          <span className={cn(
            'font-medium',
            alertLevel === 'exceeded' && 'text-red-600',
            alertLevel === 'critical' && 'text-orange-600',
            alertLevel === 'warning' && 'text-yellow-600',
            alertLevel === 'none' && 'text-green-600'
          )}>
            {quota.percentage.toFixed(0)}%
          </span>
        </div>
        <Progress 
          value={Math.min(quota.percentage, 100)} 
          className="h-2"
        />
      </div>

      <p className="text-xs text-muted-foreground">
        {quota.remaining !== null ? `${quota.remaining} remaining` : 'Unlimited'}
      </p>
    </div>
  );
}

interface UsageDetailCardProps {
  quota: QuotaStatus;
}

export function UsageDetailCard({ quota }: UsageDetailCardProps) {
  const alertLevel = getAlertLevel(quota.percentage);
  const config = FEATURE_CONFIG[quota.featureKey];

  return (
    <Card className={cn(
      'transition-all',
      alertLevel === 'exceeded' && 'border-red-200 bg-red-50/50',
      alertLevel === 'critical' && 'border-orange-200',
      alertLevel === 'warning' && 'border-yellow-200'
    )}>
      <CardHeader className="flex flex-row items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={cn(
            'p-3 rounded-lg',
            alertLevel === 'exceeded' && 'bg-red-100 text-red-600',
            alertLevel === 'critical' && 'bg-orange-100 text-orange-600',
            alertLevel === 'warning' && 'bg-yellow-100 text-yellow-600',
            alertLevel === 'none' && 'bg-blue-100 text-blue-600'
          )}>
            {FEATURE_ICONS[quota.featureKey]}
          </div>
          <div>
            <CardTitle>{quota.featureName}</CardTitle>
            <CardDescription>{config?.description}</CardDescription>
          </div>
        </div>
        {alertLevel !== 'none' && (
          <Badge
            className={cn(
              'text-sm',
              alertLevel === 'exceeded' && 'bg-red-100 text-red-800',
              alertLevel === 'critical' && 'bg-orange-100 text-orange-800',
              alertLevel === 'warning' && 'bg-yellow-100 text-yellow-800'
            )}
          >
            {alertLevel}
          </Badge>
        )}
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
          <div>
            <p className="text-3xl font-bold">{quota.used.toLocaleString()}</p>
            <p className="text-sm text-muted-foreground">
              {config?.unit} used
            </p>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold">
              {quota.isUnlimited ? '∞' : quota.limit?.toLocaleString()}
            </p>
            <p className="text-sm text-muted-foreground">/ {quota.isUnlimited ? 'unlimited' : `${quota.limit?.toLocaleString()} ${config?.unit}`}</p>
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Usage</span>
            <span className={cn(
              'text-sm font-medium',
              alertLevel === 'exceeded' && 'text-red-600',
              alertLevel === 'critical' && 'text-orange-600',
              alertLevel === 'warning' && 'text-yellow-600',
              alertLevel === 'none' && 'text-green-600'
            )}>
              {quota.percentage.toFixed(1)}%
            </span>
          </div>
          <div className="h-4 bg-muted rounded-full overflow-hidden">
            <div
              className={cn(
                'h-full rounded-full transition-all',
                alertLevel === 'exceeded' && 'bg-red-500',
                alertLevel === 'critical' && 'bg-orange-500',
                alertLevel === 'warning' && 'bg-yellow-500',
                alertLevel === 'none' && 'bg-green-500'
              )}
              style={{ width: `${Math.min(quota.percentage, 100)}%` }}
            />
          </div>
        </div>

        {quota.remaining !== null && (
          <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
            <span className="text-sm">Remaining</span>
            <span className="font-semibold">
              {quota.remaining.toLocaleString()} {config?.unit}
            </span>
          </div>
        )}

        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>Reset Period</span>
          <span className="capitalize">{quota.resetPeriod}</span>
        </div>

        {quota.nextResetAt && (
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>Next Reset</span>
            <span>{new Date(quota.nextResetAt).toLocaleDateString()}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface UsageBreakdownProps {
  className?: string;
}

export function UsageBreakdown({ className }: UsageBreakdownProps) {
  const { usageSummary } = useUsageStore();

  if (!usageSummary) return null;

  const sortedBreakdown = [...usageSummary.breakdown].sort((a, b) => b.count - a.count);

  return (
    <Card className={cn(className)}>
      <CardHeader>
        <CardTitle>Usage Breakdown</CardTitle>
        <CardDescription>
          Total usage this period: {usageSummary.totalUsage.toLocaleString()}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {sortedBreakdown.map((item) => (
            <div key={item.featureKey} className="flex items-center gap-4">
              <div className="w-8 h-8 bg-muted rounded flex items-center justify-center">
                {FEATURE_ICONS[item.featureKey as FeatureKey]}
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium">{item.featureName}</span>
                  <span className="text-sm text-muted-foreground">
                    {item.count.toLocaleString()} ({item.percentage.toFixed(1)}%)
                  </span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded-full"
                    style={{ width: `${item.percentage}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export default UsageWidget;
'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  AlertTriangle,
  AlertCircle,
  CheckCircle,
  Bell,
  BellOff,
  X,
  XCircle,
  RefreshCw,
  ChevronRight,
  Clock,
  Filter,
} from 'lucide-react';
import { QuotaAlert, AlertType } from '../types';
import { useUsageStore } from '../store';
import { ALERT_COLORS } from '../constants';
import { cn } from '@/lib/utils';

interface AlertPanelProps {
  className?: string;
}

export function AlertPanel({ className }: AlertPanelProps) {
  const { alerts, markAlertRead, dismissAlert, clearAllAlerts, isLoading } = useUsageStore();
  const [filter, setFilter] = useState<'all' | 'unread' | 'warning' | 'critical'>('all');

  const activeAlerts = alerts.filter(a => !a.isDismissed);
  const unreadAlerts = activeAlerts.filter(a => !a.isRead);
  
  const filteredAlerts = activeAlerts.filter(alert => {
    if (filter === 'all') return true;
    if (filter === 'unread') return !alert.isRead;
    if (filter === 'warning') return alert.alertType === 'warning';
    if (filter === 'critical') return alert.alertType === 'critical' || alert.alertType === 'exceeded';
    return true;
  });

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  const getAlertIcon = (type: AlertType) => {
    switch (type) {
      case 'exceeded':
        return <XCircle className="w-5 h-5" />;
      case 'critical':
        return <AlertTriangle className="w-5 h-5" />;
      case 'warning':
        return <AlertCircle className="w-5 h-5" />;
      default:
        return <Bell className="w-5 h-5" />;
    }
  };

  return (
    <Card className={cn(className)}>
      <CardHeader className="flex flex-row items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Bell className="w-5 h-5" />
            {unreadAlerts.length > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                {unreadAlerts.length}
              </span>
            )}
          </div>
          <div>
            <CardTitle>Quota Alerts</CardTitle>
            <CardDescription>Stay informed about your usage limits</CardDescription>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <select
            className="h-9 px-3 rounded-md border bg-background text-sm"
            value={filter}
            onChange={(e) => setFilter(e.target.value as any)}
          >
            <option value="all">All</option>
            <option value="unread">Unread</option>
            <option value="warning">Warning</option>
            <option value="critical">Critical</option>
          </select>
          {activeAlerts.length > 0 && (
            <Button variant="ghost" size="sm" onClick={clearAllAlerts}>
              <BellOff className="w-4 h-4" />
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent>
        {filteredAlerts.length === 0 ? (
          <div className="text-center py-8">
            <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">All Clear!</h3>
            <p className="text-muted-foreground">No quota alerts at this time.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredAlerts.map((alert) => (
              <div
                key={alert.id}
                className={cn(
                  'p-4 rounded-lg border transition-all',
                  !alert.isRead && 'bg-blue-50/50',
                  alert.alertType === 'exceeded' && ALERT_COLORS.exceeded,
                  alert.alertType === 'critical' && ALERT_COLORS.critical,
                  alert.alertType === 'warning' && ALERT_COLORS.warning
                )}
              >
                <div className="flex items-start gap-3">
                  <div className={cn(
                    'p-2 rounded-lg',
                    alert.alertType === 'exceeded' && 'bg-red-200 text-red-800',
                    alert.alertType === 'critical' && 'bg-orange-200 text-orange-800',
                    alert.alertType === 'warning' && 'bg-yellow-200 text-yellow-800'
                  )}>
                    {getAlertIcon(alert.alertType)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <h4 className="font-medium capitalize">{alert.featureKey.replace('_', ' ')}</h4>
                      <Badge variant="outline" className="text-xs">
                        {alert.alertType}
                      </Badge>
                    </div>
                    <p className="text-sm">
                      Usage at <span className="font-semibold">{alert.currentPercent}%</span> of limit
                      {alert.thresholdPercent > alert.currentPercent && (
                        <span> (threshold: {alert.thresholdPercent}%)</span>
                      )}
                    </p>
                    <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                      <Clock className="w-3 h-3" />
                      <span>{formatTime(alert.createdAt)}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    {!alert.isRead && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => markAlertRead(alert.id)}
                      >
                        <CheckCircle className="w-4 h-4" />
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => dismissAlert(alert.id)}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface AlertBadgeProps {
  count: number;
  type?: AlertType;
  className?: string;
}

export function AlertBadge({ count, type = 'warning', className }: AlertBadgeProps) {
  if (count === 0) return null;

  return (
    <span
      className={cn(
        'inline-flex items-center justify-center min-w-[20px] h-5 px-1.5 text-xs font-medium rounded-full',
        type === 'exceeded' && 'bg-red-500 text-white',
        type === 'critical' && 'bg-orange-500 text-white',
        type === 'warning' && 'bg-yellow-500 text-white',
        className
      )}
    >
      {count > 99 ? '99+' : count}
    </span>
  );
}

interface RealtimeAlertToastProps {
  alert: QuotaAlert;
  onDismiss: () => void;
  onUpgrade: () => void;
}

export function RealtimeAlertToast({ alert, onDismiss, onUpgrade }: RealtimeAlertToastProps) {
  const [visible, setVisible] = useState(true);

  if (!visible) return null;

  return (
    <div className={cn(
      'fixed bottom-4 right-4 max-w-sm p-4 rounded-lg border shadow-lg z-50 animate-in slide-in-from-bottom',
      alert.alertType === 'exceeded' && 'bg-red-50 border-red-200',
      alert.alertType === 'critical' && 'bg-orange-50 border-orange-200',
      alert.alertType === 'warning' && 'bg-yellow-50 border-yellow-200'
    )}>
      <div className="flex items-start gap-3">
        <div className={cn(
          'p-2 rounded-lg',
          alert.alertType === 'exceeded' && 'bg-red-200 text-red-800',
          alert.alertType === 'critical' && 'bg-orange-200 text-orange-800',
          alert.alertType === 'warning' && 'bg-yellow-200 text-yellow-800'
        )}>
          <AlertTriangle className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <h4 className="font-medium">Quota Alert</h4>
          <p className="text-sm mt-1">
            You've used {alert.currentPercent}% of your {alert.featureKey.replace('_', ' ')} quota.
          </p>
          <div className="flex items-center gap-2 mt-3">
            <Button size="sm" onClick={onUpgrade}>Upgrade</Button>
            <Button size="sm" variant="ghost" onClick={onDismiss}>Dismiss</Button>
          </div>
        </div>
        <button
          onClick={() => {
            setVisible(false);
            onDismiss();
          }}
          className="p-1 hover:bg-white rounded"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

export default AlertPanel;
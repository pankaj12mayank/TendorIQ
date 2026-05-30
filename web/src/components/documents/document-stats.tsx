'use client';

import { useEffect } from 'react';
import { FileText, HardDrive, AlertTriangle, Clock, CheckCircle2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useDocumentStore } from '@/stores/document-store';
import { useDocumentsApi } from '@/hooks/use-documents';
import { StatusDot } from './status-badge';

export function DocumentStats() {
  const store = useDocumentStore();
  const { fetchStats } = useDocumentsApi();

  useEffect(() => {
    fetchStats().catch((err: unknown) => {
      console.error('Failed to fetch document stats:', err);
    });
  }, [fetchStats]);

  const stats = store.stats;

  if (!stats) {
    return (
      <div className="grid gap-4 md:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <div className="h-20 animate-pulse rounded bg-muted" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const cards = [
    {
      title: 'Total Documents',
      value: stats.total_documents,
      icon: FileText,
      color: 'text-blue-500',
    },
    {
      title: 'Storage Used',
      value: `${stats.total_size_mb} MB`,
      icon: HardDrive,
      color: 'text-purple-500',
    },
    {
      title: 'Failed',
      value: stats.failed_count,
      icon: AlertTriangle,
      color: 'text-red-500',
      showDot: true,
    },
    {
      title: 'Processing',
      value: stats.pending_count,
      icon: Clock,
      color: 'text-yellow-500',
      showDot: true,
    },
  ];

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-4">
        {cards.map((card) => (
          <Card key={card.title}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {card.title}
              </CardTitle>
              <card.icon className={`h-4 w-4 ${card.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{card.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Status breakdown */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {Object.entries(stats.by_status).map(([status, count]) => (
          <Card key={status} className="relative overflow-hidden">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <StatusDot status={status as never} />
                  <span className="text-sm font-medium capitalize">{status.replace('_', ' ')}</span>
                </div>
                <span className="text-lg font-bold">{count}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quota usage */}
      {stats.quota_usage_percent > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Storage Quota</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Usage</span>
                <span className="font-medium">{stats.quota_usage_percent.toFixed(1)}%</span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className={`h-full transition-all ${
                    stats.quota_usage_percent > 90
                      ? 'bg-red-500'
                      : stats.quota_usage_percent > 70
                      ? 'bg-yellow-500'
                      : 'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(stats.quota_usage_percent, 100)}%` }}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
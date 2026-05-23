import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Activity,
  Zap,
  Clock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Pause,
  Play,
  RefreshCw,
} from 'lucide-react';
import { QueueJob } from '@/components/admin/types';
import type { PlatformHealthComponent, PlatformQueueStats } from '@/lib/admin-platform-api';
import { cn } from '@/lib/utils';

interface RealtimeQueueStatusProps {
  className?: string;
  stats?: PlatformQueueStats | null;
  isLoading?: boolean;
}

export function RealtimeQueueStatus({ className, stats, isLoading }: RealtimeQueueStatusProps) {
  const pending = stats?.pending ?? 0;
  const processing = stats?.processing ?? 0;
  const completed = stats?.completed ?? 0;
  const failed = stats?.failed ?? 0;
  const health = stats?.healthPercent ?? 100;

  return (
    <Card className={cn(className)}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-base">Queue Status</CardTitle>
        <Badge className={cn(isLoading ? 'bg-gray-100 text-gray-800' : 'bg-green-100 text-green-800')}>
          {isLoading ? 'Syncing' : 'Live'}
        </Badge>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-600">{pending}</div>
            <div className="text-xs text-muted-foreground">Pending</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{processing}</div>
            <div className="text-xs text-muted-foreground">Processing</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{completed}</div>
            <div className="text-xs text-muted-foreground">Completed</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{failed}</div>
            <div className="text-xs text-muted-foreground">Failed</div>
          </div>
        </div>
        <div className="mt-4">
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-muted-foreground">Queue Health</span>
            <span className="font-medium">{health.toFixed(1)}%</span>
          </div>
          <Progress value={health} className="h-2" />
        </div>
      </CardContent>
    </Card>
  );
}

export interface RealtimeMetricsData {
  apiCalls: number;
  activeJobs: number;
  errorRate: number;
  avgResponseTime: number;
}

interface RealtimeMetricsProps {
  className?: string;
  metrics?: RealtimeMetricsData | null;
  isLoading?: boolean;
}

export function RealtimeMetrics({ className, metrics, isLoading }: RealtimeMetricsProps) {
  const apiCalls = metrics?.apiCalls ?? 0;
  const activeJobs = metrics?.activeJobs ?? 0;
  const errorRate = metrics?.errorRate ?? 0;
  const avgResponseTime = metrics?.avgResponseTime ?? 0;

  return (
    <Card className={cn(className)}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-base">Real-time Metrics</CardTitle>
        <Activity
          className={cn('w-4 h-4', isLoading ? 'text-muted-foreground' : 'text-green-600 animate-pulse')}
        />
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Zap className="w-4 h-4 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{apiCalls.toLocaleString()}</p>
              <p className="text-xs text-muted-foreground">API Calls</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Clock className="w-4 h-4 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{avgResponseTime}ms</p>
              <p className="text-xs text-muted-foreground">Avg Response</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <AlertTriangle className="w-4 h-4 text-orange-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{errorRate.toFixed(1)}%</p>
              <p className="text-xs text-muted-foreground">Error Rate</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <Play className="w-4 h-4 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{activeJobs}</p>
              <p className="text-xs text-muted-foreground">Active Jobs</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface JobCardProps {
  job: QueueJob;
  onRetry?: (id: string) => void;
  onCancel?: (id: string) => void;
  onPause?: (id: string) => void;
}

export function JobCard({ job, onRetry, onCancel, onPause }: JobCardProps) {
  const getStatusIcon = () => {
    switch (job.status) {
      case 'processing':
        return <RefreshCw className="w-4 h-4 text-blue-600 animate-spin" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-600" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-gray-400" />;
      default:
        return <Pause className="w-4 h-4 text-yellow-600" />;
    }
  };

  const getStatusColor = () => {
    switch (job.status) {
      case 'processing':
        return 'border-blue-200 bg-blue-50';
      case 'completed':
        return 'border-green-200 bg-green-50';
      case 'failed':
        return 'border-red-200 bg-red-50';
      case 'pending':
        return 'border-gray-200 bg-gray-50';
      default:
        return 'border-yellow-200 bg-yellow-50';
    }
  };

  return (
    <div className={cn('p-4 border rounded-lg transition-all', getStatusColor())}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <h4 className="font-medium">{job.name}</h4>
        </div>
        <Badge
          className={cn(
            job.priority === 'urgent' && 'bg-red-100 text-red-800',
            job.priority === 'high' && 'bg-orange-100 text-orange-800',
            job.priority === 'normal' && 'bg-blue-100 text-blue-800',
            job.priority === 'low' && 'bg-gray-100 text-gray-800'
          )}
        >
          {job.priority}
        </Badge>
      </div>

      {job.status === 'processing' && (
        <div className="mb-3">
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-muted-foreground">Progress</span>
            <span>{job.progress}%</span>
          </div>
          <Progress value={job.progress} className="h-2" />
        </div>
      )}

      {job.error && (
        <div className="p-2 bg-red-100 rounded text-sm text-red-800 mb-3">{job.error}</div>
      )}

      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>
          Attempts: {job.attempts}/{job.maxAttempts}
        </span>
        <div className="flex gap-1">
          {job.status === 'failed' && job.retryable && onRetry && (
            <button type="button" onClick={() => onRetry(job.id)} className="p-1 hover:bg-white rounded">
              <RefreshCw className="w-4 h-4" />
            </button>
          )}
          {job.status === 'pending' && onPause && (
            <button type="button" onClick={() => onPause(job.id)} className="p-1 hover:bg-white rounded">
              <Pause className="w-4 h-4" />
            </button>
          )}
          {onCancel && (
            <button type="button" onClick={() => onCancel(job.id)} className="p-1 hover:bg-white rounded">
              <XCircle className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

interface SystemHealthProps {
  className?: string;
  components?: PlatformHealthComponent[];
  isLoading?: boolean;
}

export function SystemHealth({ className, components, isLoading }: SystemHealthProps) {
  const rows = components?.length
    ? components
    : [{ name: 'Platform', status: isLoading ? 'unknown' : 'degraded', uptime: 0 }];

  return (
    <Card className={cn(className)}>
      <CardHeader>
        <CardTitle className="text-base">System Health</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {rows.map((component) => (
            <div key={component.name} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div
                  className={cn(
                    'w-2 h-2 rounded-full',
                    component.status === 'healthy' ? 'bg-green-500' : 'bg-yellow-500'
                  )}
                />
                <span className="text-sm font-medium">{component.name}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">{component.uptime}%</span>
                <Badge
                  className={cn(
                    'text-xs',
                    component.status === 'healthy' && 'bg-green-100 text-green-800',
                    component.status !== 'healthy' && 'bg-yellow-100 text-yellow-800'
                  )}
                >
                  {component.status}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export default {
  RealtimeQueueStatus,
  RealtimeMetrics,
  JobCard,
  SystemHealth,
};

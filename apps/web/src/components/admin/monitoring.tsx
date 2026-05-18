import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Activity,
  Zap,
  Clock,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  CheckCircle,
  XCircle,
  Pause,
  Play,
  RefreshCw,
} from 'lucide-react';
import { QueueJob } from '@/components/admin/types';
import { cn } from '@/lib/utils';

interface RealtimeQueueStatusProps {
  className?: string;
}

export function RealtimeQueueStatus({ className }: RealtimeQueueStatusProps) {
  const stats = {
    pending: 5,
    processing: 12,
    completed: 89,
    failed: 3,
    total: 109,
  };

  return (
    <Card className={cn(className)}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-base">Queue Status</CardTitle>
        <Badge className="bg-green-100 text-green-800 animate-pulse">Live</Badge>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-600">{stats.pending}</div>
            <div className="text-xs text-muted-foreground">Pending</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{stats.processing}</div>
            <div className="text-xs text-muted-foreground">Processing</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{stats.completed}</div>
            <div className="text-xs text-muted-foreground">Completed</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{stats.failed}</div>
            <div className="text-xs text-muted-foreground">Failed</div>
          </div>
        </div>
        <div className="mt-4">
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-muted-foreground">Queue Health</span>
            <span className="font-medium">98.2%</span>
          </div>
          <Progress value={98.2} className="h-2" />
        </div>
      </CardContent>
    </Card>
  );
}

interface RealtimeMetricsProps {
  className?: string;
}

export function RealtimeMetrics({ className }: RealtimeMetricsProps) {
  const [metrics, setMetrics] = React.useState({
    apiCalls: 2150,
    activeJobs: 12,
    errorRate: 0.5,
    avgResponseTime: 245,
  });

  React.useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(prev => ({
        apiCalls: prev.apiCalls + Math.floor(Math.random() * 10) - 3,
        activeJobs: Math.max(0, prev.activeJobs + Math.floor(Math.random() * 3) - 1),
        errorRate: Math.max(0, Math.min(5, prev.errorRate + (Math.random() - 0.5) * 0.2)),
        avgResponseTime: Math.max(100, Math.min(500, prev.avgResponseTime + Math.floor(Math.random() * 40) - 20)),
      }));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <Card className={cn(className)}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-base">Real-time Metrics</CardTitle>
        <Activity className="w-4 h-4 text-green-600 animate-pulse" />
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Zap className="w-4 h-4 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{metrics.apiCalls.toLocaleString()}</p>
              <p className="text-xs text-muted-foreground">API Calls</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Clock className="w-4 h-4 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{metrics.avgResponseTime}ms</p>
              <p className="text-xs text-muted-foreground">Avg Response</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <AlertTriangle className="w-4 h-4 text-orange-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{metrics.errorRate.toFixed(1)}%</p>
              <p className="text-xs text-muted-foreground">Error Rate</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <Play className="w-4 h-4 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{metrics.activeJobs}</p>
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
        <Badge className={cn(
          job.priority === 'urgent' && 'bg-red-100 text-red-800',
          job.priority === 'high' && 'bg-orange-100 text-orange-800',
          job.priority === 'normal' && 'bg-blue-100 text-blue-800',
          job.priority === 'low' && 'bg-gray-100 text-gray-800'
        )}>
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
        <div className="p-2 bg-red-100 rounded text-sm text-red-800 mb-3">
          {job.error}
        </div>
      )}

      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>Attempts: {job.attempts}/{job.maxAttempts}</span>
        <div className="flex gap-1">
          {job.status === 'failed' && job.retryable && onRetry && (
            <button
              onClick={() => onRetry(job.id)}
              className="p-1 hover:bg-white rounded"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          )}
          {onCancel && (
            <button
              onClick={() => onCancel(job.id)}
              className="p-1 hover:bg-white rounded"
            >
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
}

export function SystemHealth({ className }: SystemHealthProps) {
  const components = [
    { name: 'API Server', status: 'healthy', uptime: 99.9 },
    { name: 'Database', status: 'healthy', uptime: 99.95 },
    { name: 'Queue Worker', status: 'healthy', uptime: 98.5 },
    { name: 'AI Service', status: 'degraded', uptime: 95.0 },
    { name: 'Storage', status: 'healthy', uptime: 99.99 },
  ];

  return (
    <Card className={cn(className)}>
      <CardHeader>
        <CardTitle className="text-base">System Health</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {components.map((component) => (
            <div key={component.name} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className={cn(
                  'w-2 h-2 rounded-full',
                  component.status === 'healthy' ? 'bg-green-500' : 'bg-yellow-500'
                )} />
                <span className="text-sm font-medium">{component.name}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">{component.uptime}%</span>
                <Badge
                  className={cn(
                    'text-xs',
                    component.status === 'healthy' && 'bg-green-100 text-green-800',
                    component.status === 'degraded' && 'bg-yellow-100 text-yellow-800'
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
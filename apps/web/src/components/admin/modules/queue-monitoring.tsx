'use client';

import React, { useState, useEffect } from 'react';
import { useQueueApi } from '@/hooks/use-admin';
import { LoadingState } from '@/components/ui/loading-state';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  List,
  Play,
  Pause,
  RotateCcw,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  RefreshCw,
  Search,
  Filter,
  MoreHorizontal,
} from 'lucide-react';
import { QueueJob } from '../types';
import { cn } from '@/lib/utils';

const JOB_STATUS_COLORS = {
  pending: 'bg-gray-100 text-gray-800',
  processing: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  retry: 'bg-yellow-100 text-yellow-800',
};

const PRIORITY_COLORS = {
  low: 'bg-gray-100 text-gray-800',
  normal: 'bg-blue-100 text-blue-800',
  high: 'bg-orange-100 text-orange-800',
  urgent: 'bg-red-100 text-red-800',
};

export function QueueMonitoring() {
  const { jobs, isLoading, refreshJobs, retryJob, cancelJob } = useQueueApi();
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const filteredJobs = jobs.filter((job) => {
    const matchesSearch = job.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      job.id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = !statusFilter || job.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const stats = {
    pending: jobs.filter((j) => j.status === 'pending').length,
    processing: jobs.filter((j) => j.status === 'processing').length,
    completed: jobs.filter((j) => j.status === 'completed').length,
    failed: jobs.filter((j) => j.status === 'failed').length,
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  useEffect(() => {
    void refreshJobs();
    const t = setInterval(() => void refreshJobs(), 15000);
    return () => clearInterval(t);
  }, [refreshJobs]);

  if (isLoading && jobs.length === 0) {
    return <LoadingState message="Loading queue..." />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Queue Monitoring</h2>
          <p className="text-muted-foreground">Monitor and manage background jobs</p>
        </div>
        <Button variant="outline" onClick={() => void refreshJobs()}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card className="bg-blue-50 border-blue-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-blue-800">Pending</CardTitle>
            <Clock className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">{stats.pending}</div>
          </CardContent>
        </Card>

        <Card className="bg-blue-50 border-blue-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-blue-800">Processing</CardTitle>
            <Play className="h-4 w-4 text-blue-600 animate-pulse" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">{stats.processing}</div>
          </CardContent>
        </Card>

        <Card className="bg-green-50 border-green-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-green-800">Completed</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">{stats.completed}</div>
          </CardContent>
        </Card>

        <Card className="bg-red-50 border-red-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-red-800">Failed</CardTitle>
            <XCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-red-600">{stats.failed}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Active Jobs</CardTitle>
            <div className="flex items-center gap-4">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search jobs..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              <select
                className="h-10 px-3 rounded-md border bg-background text-sm"
                value={statusFilter || ''}
                onChange={(e) => setStatusFilter(e.target.value || null)}
              >
                <option value="">All Status</option>
                <option value="pending">Pending</option>
                <option value="processing">Processing</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
                <option value="retry">Retry</option>
              </select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredJobs.map((job) => (
              <div key={job.id} className="p-4 border rounded-lg">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      'w-10 h-10 rounded-lg flex items-center justify-center',
                      job.status === 'processing' && 'bg-blue-100',
                      job.status === 'completed' && 'bg-green-100',
                      job.status === 'failed' && 'bg-red-100',
                      job.status === 'pending' && 'bg-gray-100',
                      job.status === 'retry' && 'bg-yellow-100'
                    )}>
                      {job.status === 'processing' && <Play className="w-5 h-5 text-blue-600 animate-pulse" />}
                      {job.status === 'completed' && <CheckCircle className="w-5 h-5 text-green-600" />}
                      {job.status === 'failed' && <XCircle className="w-5 h-5 text-red-600" />}
                      {job.status === 'pending' && <Clock className="w-5 h-5 text-gray-400" />}
                      {job.status === 'retry' && <RefreshCw className="w-5 h-5 text-yellow-600" />}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold">{job.name}</h3>
                        <Badge className={JOB_STATUS_COLORS[job.status]}>{job.status}</Badge>
                        <Badge className={PRIORITY_COLORS[job.priority]}>{job.priority}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">ID: {job.id}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {job.status === 'failed' && job.retryable && (
                      <Button variant="outline" size="sm" onClick={() => void retryJob(job.id)}>
                        <RotateCcw className="w-4 h-4 mr-2" />
                        Retry
                      </Button>
                    )}
                    <Button variant="ghost" size="sm">
                      <MoreHorizontal className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                {job.status === 'processing' && (
                  <div className="mb-3">
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-muted-foreground">Progress</span>
                      <span>{job.progress}%</span>
                    </div>
                    <Progress value={job.progress} />
                  </div>
                )}

                <div className="grid gap-4 md:grid-cols-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Queue</span>
                    <p className="font-medium">{job.queue}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Attempts</span>
                    <p className="font-medium">{job.attempts}/{job.maxAttempts}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Worker</span>
                    <p className="font-medium">{job.worker || '-'}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Created</span>
                    <p className="font-medium">{formatDate(job.createdAt)}</p>
                  </div>
                </div>

                {job.error && (
                  <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex items-center gap-2 text-red-800 mb-1">
                      <AlertTriangle className="w-4 h-4" />
                      <span className="text-sm font-medium">Error</span>
                    </div>
                    <p className="text-sm text-red-600">{job.error}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default QueueMonitoring;
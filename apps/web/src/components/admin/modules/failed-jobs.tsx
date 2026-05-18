'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  AlertCircle,
  RotateCcw,
  Trash2,
  Search,
  Filter,
  Clock,
  RefreshCw,
  Play,
  XCircle,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
} from 'lucide-react';
import { FailedJob } from '../types';
import { MOCK_FAILED_JOBS } from '../constants';
import { cn } from '@/lib/utils';

const QUEUE_COLORS = {
  ai: 'bg-purple-100 text-purple-800',
  documents: 'bg-blue-100 text-blue-800',
  notifications: 'bg-green-100 text-green-800',
  exports: 'bg-orange-100 text-orange-800',
};

export function FailedJobs() {
  const [jobs, setJobs] = useState<FailedJob[]>(MOCK_FAILED_JOBS);
  const [searchQuery, setSearchQuery] = useState('');
  const [queueFilter, setQueueFilter] = useState<string | null>(null);
  const [expandedJob, setExpandedJob] = useState<string | null>(null);

  const filteredJobs = jobs.filter((job) => {
    const matchesSearch = job.jobName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      job.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      job.error.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesQueue = !queueFilter || job.queue === queueFilter;
    return matchesSearch && matchesQueue;
  });

  const stats = {
    total: jobs.length,
    retryable: jobs.filter((j) => j.retryable).length,
    nonRetryable: jobs.filter((j) => !j.retryable).length,
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const retryJob = (id: string) => {
    setJobs(jobs.filter((j) => j.id !== id));
  };

  const retryAll = () => {
    setJobs(jobs.filter((j) => !j.retryable));
  };

  const deleteJob = (id: string) => {
    setJobs(jobs.filter((j) => j.id !== id));
  };

  const clearAll = () => {
    setJobs([]);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Failed Jobs</h2>
          <p className="text-muted-foreground">Manage and retry failed background jobs</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={retryAll} disabled={stats.retryable === 0}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Retry All ({stats.retryable})
          </Button>
          <Button variant="destructive" onClick={clearAll} disabled={jobs.length === 0}>
            <Trash2 className="w-4 h-4 mr-2" />
            Clear All
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="bg-red-50 border-red-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-red-800">Total Failed</CardTitle>
            <AlertCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-red-600">{stats.total}</div>
          </CardContent>
        </Card>

        <Card className="bg-yellow-50 border-yellow-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-yellow-800">Retryable</CardTitle>
            <RefreshCw className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-yellow-600">{stats.retryable}</div>
          </CardContent>
        </Card>

        <Card className="bg-gray-50 border-gray-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-800">Non-Retryable</CardTitle>
            <XCircle className="h-4 w-4 text-gray-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-600">{stats.nonRetryable}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Failed Job List</CardTitle>
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
                value={queueFilter || ''}
                onChange={(e) => setQueueFilter(e.target.value || null)}
              >
                <option value="">All Queues</option>
                <option value="ai">AI</option>
                <option value="documents">Documents</option>
                <option value="notifications">Notifications</option>
                <option value="exports">Exports</option>
              </select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {filteredJobs.length === 0 ? (
            <div className="text-center py-12">
              <AlertCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">No Failed Jobs</h3>
              <p className="text-muted-foreground">All jobs are running smoothly.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredJobs.map((job) => (
                <div
                  key={job.id}
                  className={cn(
                    'p-4 border rounded-lg transition-all cursor-pointer',
                    expandedJob === job.id ? 'bg-red-50/50' : 'hover:bg-muted/30'
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                      <div className="w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center">
                        <XCircle className="w-5 h-5 text-red-600" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold">{job.jobName}</h3>
                          <Badge className={QUEUE_COLORS[job.queue as keyof typeof QUEUE_COLORS] || 'bg-gray-100'}>
                            {job.queue}
                          </Badge>
                          <Badge variant={job.retryable ? 'default' : 'destructive'}>
                            {job.retryable ? 'Retryable' : 'Non-Retryable'}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mb-2">
                          ID: {job.id}
                        </p>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {formatDate(job.failedAt)}
                          </span>
                          <span>Attempts: {job.attemptCount}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {job.retryable && (
                        <Button variant="outline" size="sm" onClick={() => retryJob(job.id)}>
                          <RotateCcw className="w-4 h-4 mr-2" />
                          Retry
                        </Button>
                      )}
                      <Button variant="ghost" size="sm" onClick={() => setExpandedJob(expandedJob === job.id ? null : job.id)}>
                        {expandedJob === job.id ? (
                          <ChevronDown className="w-4 h-4" />
                        ) : (
                          <ChevronRight className="w-4 h-4" />
                        )}
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => deleteJob(job.id)}>
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>

                  <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex items-center gap-2 text-red-800 mb-1">
                      <AlertTriangle className="w-4 h-4" />
                      <span className="text-sm font-medium">Error</span>
                    </div>
                    <p className="text-sm text-red-600">{job.error}</p>
                  </div>

                  {expandedJob === job.id && (
                    <div className="mt-4 pt-4 border-t space-y-3">
                      <div className="grid gap-4 md:grid-cols-2">
                        <div>
                          <span className="text-xs text-muted-foreground uppercase tracking-wide">Last Attempt</span>
                          <p className="text-sm">{formatDate(job.lastAttemptAt)}</p>
                        </div>
                        <div>
                          <span className="text-xs text-muted-foreground uppercase tracking-wide">Failed At</span>
                          <p className="text-sm">{formatDate(job.failedAt)}</p>
                        </div>
                      </div>
                      <div>
                        <span className="text-xs text-muted-foreground uppercase tracking-wide">Payload</span>
                        <pre className="mt-1 p-3 bg-muted rounded-lg text-sm overflow-x-auto">
                          {JSON.stringify(job.payload, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default FailedJobs;
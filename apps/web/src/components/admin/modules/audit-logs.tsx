'use client';

import React, { useState, useEffect } from 'react';
import { useAuditLogApi } from '@/hooks/use-admin';
import { LoadingState } from '@/components/ui/loading-state';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Search,
  Download,
  ChevronDown,
  User,
  Clock,
  Monitor,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { ROLE_COLORS } from '../constants';

const ACTION_COLORS: Record<string, string> = {
  USER_CREATED: 'bg-green-100 text-green-800',
  USER_DELETED: 'bg-red-100 text-red-800',
  USER_ROLE_CHANGED: 'bg-blue-100 text-blue-800',
  SETTINGS_UPDATED: 'bg-purple-100 text-purple-800',
  PROMPT_UPDATED: 'bg-orange-100 text-orange-800',
  BILLING_UPDATED: 'bg-yellow-100 text-yellow-800',
  login: 'bg-slate-100 text-slate-800',
  delete: 'bg-red-100 text-red-800',
};

export function AuditLogs() {
  const { logs, isLoading, fetchLogs, exportLogs } = useAuditLogApi();
  const [searchQuery, setSearchQuery] = useState('');
  const [actionFilter, setActionFilter] = useState<string | null>(null);
  const [expandedLog, setExpandedLog] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  useEffect(() => {
    void fetchLogs();
  }, [fetchLogs]);

  if (isLoading && logs.length === 0) {
    return <LoadingState message="Loading audit logs..." />;
  }

  const filteredLogs = logs.filter((log) => {
    const matchesSearch =
      log.userName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.details.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.resource.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesAction = !actionFilter || log.action.includes(actionFilter);
    return matchesSearch && matchesAction;
  });

  const paginatedLogs = filteredLogs.slice((currentPage - 1) * pageSize, currentPage * pageSize);
  const totalPages = Math.ceil(filteredLogs.length / pageSize) || 1;

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const uniqueActions = [...new Set(logs.map((l) => l.action.split('_')[0]))];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Audit Logs</h2>
          <p className="text-muted-foreground">Complete history of all system actions</p>
        </div>
        <Button variant="outline" onClick={() => void exportLogs('csv')}>
          <Download className="w-4 h-4 mr-2" />
          Export Logs
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search logs..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              <select
                className="h-10 px-3 rounded-md border bg-background text-sm"
                value={actionFilter || ''}
                onChange={(e) => setActionFilter(e.target.value || null)}
              >
                <option value="">All Actions</option>
                {uniqueActions.map((action) => (
                  <option key={action} value={action}>
                    {action}
                  </option>
                ))}
              </select>
            </div>
            <p className="text-sm text-muted-foreground">{filteredLogs.length} entries</p>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {paginatedLogs.map((log) => (
              <div
                key={log.id}
                className={cn(
                  'p-4 border rounded-lg transition-all cursor-pointer',
                  expandedLog === log.id ? 'bg-muted/50' : 'hover:bg-muted/30'
                )}
                onClick={() => setExpandedLog(expandedLog === log.id ? null : log.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center">
                      <User className="w-5 h-5 text-muted-foreground" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-medium">{log.userName}</h3>
                        <Badge className={ROLE_COLORS[log.userRole as keyof typeof ROLE_COLORS]}>
                          {log.userRole.replace('_', ' ')}
                        </Badge>
                        <Badge className={ACTION_COLORS[log.action] || 'bg-gray-100'}>
                          {log.action.replace('_', ' ')}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">{log.details}</p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Monitor className="w-3 h-3" />
                          {log.resource}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {formatTimestamp(log.timestamp)}
                        </span>
                        <span>{log.ipAddress}</span>
                      </div>
                    </div>
                  </div>
                  <ChevronDown
                    className={cn(
                      'w-5 h-5 text-muted-foreground transition-transform',
                      expandedLog === log.id && 'rotate-180'
                    )}
                  />
                </div>

                {expandedLog === log.id && (
                  <div className="mt-4 pt-4 border-t space-y-3">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <span className="text-xs text-muted-foreground uppercase tracking-wide">
                          Resource ID
                        </span>
                        <p className="text-sm font-mono">{log.resourceId || '-'}</p>
                      </div>
                      <div>
                        <span className="text-xs text-muted-foreground uppercase tracking-wide">
                          User Agent
                        </span>
                        <p className="text-sm">{log.userAgent}</p>
                      </div>
                    </div>
                    {log.previousState && log.newState && (
                      <div className="grid gap-4 md:grid-cols-2">
                        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                          <span className="text-xs text-red-800 uppercase tracking-wide">
                            Previous State
                          </span>
                          <pre className="text-xs mt-1 text-red-600">
                            {JSON.stringify(log.previousState, null, 2)}
                          </pre>
                        </div>
                        <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                          <span className="text-xs text-green-800 uppercase tracking-wide">
                            New State
                          </span>
                          <pre className="text-xs mt-1 text-green-600">
                            {JSON.stringify(log.newState, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>

          {filteredLogs.length > pageSize && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-muted-foreground">
                Page {currentPage} of {totalPages}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  const page = i + 1;
                  return (
                    <Button
                      key={page}
                      variant={currentPage === page ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setCurrentPage(page)}
                    >
                      {page}
                    </Button>
                  );
                })}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default AuditLogs;

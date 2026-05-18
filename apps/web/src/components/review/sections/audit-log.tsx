'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Search,
  Filter,
  Download,
  ChevronDown,
  ChevronRight,
  Clock,
  User,
  Edit3,
  CheckCircle,
  MessageSquare,
  ArrowRight,
  RotateCcw
} from 'lucide-react';
import { AuditEntry } from '../types';
import { useReviewStore } from '../store';
import { AUDIT_ACTIONS } from '../constants';
import { cn } from '@/lib/utils';

interface AuditLogProps {
  className?: string;
}

export function AuditLog({ className }: AuditLogProps) {
  const { session, toggleAuditLog, showAuditLog } = useReviewStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterAction, setFilterAction] = useState<string | null>(null);

  if (!session) return null;

  const auditLog = session.auditLog;

  const filteredLogs = auditLog.filter(entry => {
    const matchesSearch = entry.details.toLowerCase().includes(searchQuery.toLowerCase()) ||
      entry.performedByName.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesAction = !filterAction || entry.action.includes(filterAction);
    return matchesSearch && matchesAction;
  });

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getActionIcon = (action: string) => {
    if (action.includes('EDITED')) return <Edit3 className="w-4 h-4" />;
    if (action.includes('REGENERATED')) return <RotateCcw className="w-4 h-4" />;
    if (action.includes('COMMENT')) return <MessageSquare className="w-4 h-4" />;
    if (action.includes('APPROVED')) return <CheckCircle className="w-4 h-4" />;
    if (action.includes('STARTED')) return <Clock className="w-4 h-4" />;
    return <ArrowRight className="w-4 h-4" />;
  };

  const getActionColor = (action: string) => {
    if (action.includes('REJECTED')) return 'text-red-600 bg-red-100';
    if (action.includes('REGENERATED')) return 'text-purple-600 bg-purple-100';
    if (action.includes('EDITED')) return 'text-blue-600 bg-blue-100';
    if (action.includes('COMMENT')) return 'text-yellow-600 bg-yellow-100';
    if (action.includes('APPROVED')) return 'text-green-600 bg-green-100';
    return 'text-gray-600 bg-gray-100';
  };

  const uniqueActions = [...new Set(auditLog.map(e => e.action.split('_')[0]))];

  return (
    <Card className={cn(className)}>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Audit Log
          </CardTitle>
          <CardDescription>Complete history of all actions</CardDescription>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={toggleAuditLog}>
            {showAuditLog ? 'Hide' : 'Show'}
          </Button>
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </CardHeader>

      {showAuditLog && (
        <>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search audit log..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              <select
                className="h-10 px-3 rounded-md border bg-background text-sm"
                value={filterAction || ''}
                onChange={(e) => setFilterAction(e.target.value || null)}
              >
                <option value="">All Actions</option>
                {uniqueActions.map(action => (
                  <option key={action} value={action}>{action}</option>
                ))}
              </select>
            </div>

            <div className="space-y-2 max-h-[400px] overflow-y-auto">
              {filteredLogs.map((entry) => (
                <div
                  key={entry.id}
                  className="flex items-start gap-4 p-3 rounded-lg border bg-card hover:bg-muted/50 transition-colors"
                >
                  <div className={cn('p-2 rounded-lg flex-shrink-0', getActionColor(entry.action))}>
                    {getActionIcon(entry.action)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <Badge variant="outline" className="text-xs">
                        {AUDIT_ACTIONS[entry.action as keyof typeof AUDIT_ACTIONS] || entry.action}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {formatTimestamp(entry.timestamp)}
                      </span>
                    </div>
                    <p className="text-sm">{entry.details}</p>
                    <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                      <User className="w-3 h-3" />
                      <span>{entry.performedByName}</span>
                      <span className="text-muted-foreground/50">({entry.performedByRole})</span>
                    </div>
                    {entry.previousState && entry.newState && (
                      <div className="mt-2 p-2 bg-muted rounded text-xs">
                        <span className="text-muted-foreground">Changed: </span>
                        {Object.keys(entry.previousState).map(key => (
                          <span key={key}>
                            <span className="line-through text-red-600">{String(entry.previousState[key])}</span>
                            {' → '}
                            <span className="text-green-600">{String(entry.newState[key])}</span>
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {filteredLogs.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                No audit entries found
              </div>
            )}
          </CardContent>
        </>
      )}
    </Card>
  );
}

export default AuditLog;
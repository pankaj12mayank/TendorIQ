'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  History,
  ChevronDown,
  ChevronUp,
  User,
  Clock,
  ArrowRight,
  RotateCcw,
  Eye
} from 'lucide-react';
import { ChangeRecord } from '../types';
import { useReviewStore } from '../store';
import { cn } from '@/lib/utils';

interface ChangeHistoryProps {
  className?: string;
}

export function ChangeHistory({ className }: ChangeHistoryProps) {
  const { session, showChangeHistory, toggleChangeHistory } = useReviewStore();
  const [expandedChange, setExpandedChange] = useState<string | null>(null);

  if (!session) return null;

  const changes = session.changes;

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getChangeType = (change: ChangeRecord) => {
    if (change.field.includes('isMet') || change.field.includes('isCompliant')) return 'status';
    if (change.field.includes('Value') || change.field.includes('amount')) return 'financial';
    if (change.field.includes('mitigation')) return 'risk';
    return 'general';
  };

  const getChangeTypeBadge = (type: string) => {
    switch (type) {
      case 'status':
        return <Badge variant="outline" className="text-blue-600 border-blue-300">Status</Badge>;
      case 'financial':
        return <Badge variant="outline" className="text-green-600 border-green-300">Financial</Badge>;
      case 'risk':
        return <Badge variant="outline" className="text-orange-600 border-orange-300">Risk</Badge>;
      default:
        return <Badge variant="outline">General</Badge>;
    }
  };

  return (
    <Card className={cn(className)}>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            <History className="w-5 h-5" />
            Change History
          </CardTitle>
          <CardDescription>Track all modifications made to sections</CardDescription>
        </div>
        <Button variant="outline" size="sm" onClick={toggleChangeHistory}>
          {showChangeHistory ? 'Hide' : 'Show'}
        </Button>
      </CardHeader>

      {showChangeHistory && (
        <CardContent>
          <div className="space-y-4">
            {changes.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No changes recorded yet
              </div>
            ) : (
              changes.map((change) => {
                const isExpanded = expandedChange === change.id;
                const changeType = getChangeType(change);

                return (
                  <div
                    key={change.id}
                    className="p-4 rounded-lg border bg-card hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary" className="capitalize">
                          {change.section.replace('_', ' ')}
                        </Badge>
                        {getChangeTypeBadge(changeType)}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setExpandedChange(isExpanded ? null : change.id)}
                      >
                        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </Button>
                    </div>

                    <div className="flex items-center gap-4 text-sm">
                      <div className="flex items-center gap-1 text-muted-foreground">
                        <User className="w-4 h-4" />
                        <span>{change.changedByName}</span>
                      </div>
                      <div className="flex items-center gap-1 text-muted-foreground">
                        <Clock className="w-4 h-4" />
                        <span>{formatTimestamp(change.changedAt)}</span>
                      </div>
                    </div>

                    {isExpanded && (
                      <div className="mt-4 space-y-3 pt-4 border-t">
                        <div>
                          <span className="text-xs text-muted-foreground uppercase tracking-wide">
                            Field Changed
                          </span>
                          <p className="text-sm font-medium">{change.field}</p>
                        </div>

                        <div>
                          <span className="text-xs text-muted-foreground uppercase tracking-wide">
                            Previous Value
                          </span>
                          <div className="p-2 bg-red-50 border border-red-200 rounded text-sm line-through text-red-600">
                            {change.previousValue}
                          </div>
                        </div>

                        <div>
                          <span className="text-xs text-muted-foreground uppercase tracking-wide">
                            New Value
                          </span>
                          <div className="p-2 bg-green-50 border border-green-200 rounded text-sm text-green-600">
                            {change.newValue}
                          </div>
                        </div>

                        {change.reason && (
                          <div>
                            <span className="text-xs text-muted-foreground uppercase tracking-wide">
                              Reason
                            </span>
                            <p className="text-sm italic text-muted-foreground">"{change.reason}"</p>
                          </div>
                        )}

                        <div className="flex gap-2 pt-2">
                          <Button variant="outline" size="sm">
                            <RotateCcw className="w-4 h-4 mr-2" />
                            Revert
                          </Button>
                          <Button variant="outline" size="sm">
                            <Eye className="w-4 h-4 mr-2" />
                            View Details
                          </Button>
                        </div>
                      </div>
                    )}

                    {!isExpanded && (
                      <div className="mt-2 flex items-center gap-2">
                        <span className="text-sm text-muted-foreground">Changed:</span>
                        <span className="text-sm line-through text-red-600">{change.previousValue}</span>
                        <ArrowRight className="w-4 h-4 text-muted-foreground" />
                        <span className="text-sm text-green-600">{change.newValue}</span>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>

          <div className="mt-4 pt-4 border-t">
            <h4 className="text-sm font-medium mb-3">Change Summary</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-muted rounded-lg">
                <div className="text-2xl font-bold">{changes.length}</div>
                <div className="text-xs text-muted-foreground">Total Changes</div>
              </div>
              <div className="text-center p-3 bg-muted rounded-lg">
                <div className="text-2xl font-bold">
                  {changes.filter(c => c.section === 'financial').length}
                </div>
                <div className="text-xs text-muted-foreground">Financial</div>
              </div>
              <div className="text-center p-3 bg-muted rounded-lg">
                <div className="text-2xl font-bold">
                  {changes.filter(c => c.section === 'technical').length}
                </div>
                <div className="text-xs text-muted-foreground">Technical</div>
              </div>
              <div className="text-center p-3 bg-muted rounded-lg">
                <div className="text-2xl font-bold">
                  {changes.filter(c => c.section === 'risks').length}
                </div>
                <div className="text-xs text-muted-foreground">Risks</div>
              </div>
            </div>
          </div>
        </CardContent>
      )}
    </Card>
  );
}

export default ChangeHistory;
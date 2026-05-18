'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Clock, Edit3, Save, X, Calendar, AlertCircle, CheckCircle } from 'lucide-react';
import { DeadlinesData, DeadlineItem } from '../types';
import { useAnalysisStore, getConfidenceColor } from '../store';
import { cn } from '@/lib/utils';

interface DeadlinesSectionProps {
  data: DeadlinesData;
  isEditing?: boolean;
}

const TYPE_ICONS = {
  submission: Calendar,
  clarification: Edit3,
  presentation: CheckCircle,
  contract: Calendar,
  other: Clock,
};

const TYPE_COLORS = {
  submission: 'bg-blue-100 text-blue-600',
  clarification: 'bg-purple-100 text-purple-600',
  presentation: 'bg-green-100 text-green-600',
  contract: 'bg-orange-100 text-orange-600',
  other: 'bg-gray-100 text-gray-600',
};

export function DeadlinesSection({ data, isEditing = false }: DeadlinesSectionProps) {
  const upcomingCount = data.deadlines.filter(d => d.daysRemaining <= 7 && d.daysRemaining > 0).length;
  const passedCount = data.deadlines.filter(d => d.daysRemaining < 0).length;
  const metCount = data.deadlines.filter(d => d.isMet === true).length;

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const getDaysRemainingLabel = (days: number) => {
    if (days < 0) return `${Math.abs(days)} days ago`;
    if (days === 0) return 'Today';
    if (days === 1) return 'Tomorrow';
    return `${days} days`;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-blue-100 rounded-lg">
            <Clock className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h2 className="text-2xl font-bold">Key Deadlines</h2>
            <p className="text-muted-foreground">Important dates and milestones</p>
          </div>
        </div>
        {!isEditing && (
          <Button variant="outline" size="sm">
            <Edit3 className="w-4 h-4 mr-2" />
            Edit
          </Button>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card className={upcomingCount > 0 ? 'border-red-200 bg-red-50' : ''}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Urgent</CardTitle>
            <AlertCircle className={cn('h-4 w-4', upcomingCount > 0 ? 'text-red-600' : 'text-muted-foreground')} />
          </CardHeader>
          <CardContent>
            <div className={cn('text-3xl font-bold', upcomingCount > 0 ? 'text-red-600' : '')}>{upcomingCount}</div>
            <p className="text-xs text-muted-foreground">Due within 7 days</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Deadlines</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{data.deadlines.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">{metCount}</div>
            <p className="text-xs text-muted-foreground">Met on time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">AI Confidence</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={cn('text-2xl font-bold', getConfidenceColor(data.overallConfidence.value))}>
              {data.overallConfidence.value}%
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Timeline</CardTitle>
          <CardDescription>{data.summary}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="relative">
            <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-border" />
            <div className="space-y-4">
              {data.deadlines
                .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
                .map((deadline) => {
                  const IconComponent = TYPE_ICONS[deadline.type];
                  const isUrgent = deadline.daysRemaining <= 7 && deadline.daysRemaining > 0;
                  const isPast = deadline.daysRemaining < 0;

                  return (
                    <div key={deadline.id} className="relative flex items-start gap-4 pl-16">
                      <div className={cn(
                        'absolute left-2 w-8 h-8 rounded-full flex items-center justify-center z-10',
                        TYPE_COLORS[deadline.type],
                        isUrgent && 'ring-2 ring-red-500 ring-offset-2'
                      )}>
                        <IconComponent className="w-4 h-4" />
                      </div>
                      <div className="flex-1 p-4 rounded-lg border bg-card">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium">{deadline.name}</h4>
                          <Badge variant="outline" className="text-xs">
                            {deadline.type.replace('_', ' ')}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-4 text-sm">
                          <div className="flex items-center gap-1">
                            <Calendar className="w-4 h-4 text-muted-foreground" />
                            <span>{formatDate(deadline.date)}</span>
                          </div>
                          <Badge className={cn(
                            'text-xs',
                            isPast && 'bg-gray-100 text-gray-800',
                            deadline.daysRemaining === 0 && 'bg-yellow-100 text-yellow-800',
                            isUrgent && 'bg-red-100 text-red-800',
                            !isPast && !isUrgent && deadline.daysRemaining > 7 && 'bg-green-100 text-green-800'
                          )}>
                            {getDaysRemainingLabel(deadline.daysRemaining)}
                          </Badge>
                        </div>
                        {deadline.notes && (
                          <p className="text-sm text-muted-foreground mt-2">{deadline.notes}</p>
                        )}
                        {deadline.isMet !== null && (
                          <div className="mt-2 flex items-center gap-2">
                            {deadline.isMet ? (
                              <span className="text-xs text-green-600 flex items-center gap-1">
                                <CheckCircle className="w-3 h-3" /> Met
                              </span>
                            ) : (
                              <span className="text-xs text-gray-600">Pending</span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>
        </CardContent>
      </Card>

      {isEditing && (
        <div className="flex justify-end gap-2 pt-4 border-t">
          <Button variant="outline">
            <X className="w-4 h-4 mr-2" />
            Cancel
          </Button>
          <Button>
            <Save className="w-4 h-4 mr-2" />
            Save Changes
          </Button>
        </div>
      )}
    </div>
  );
}

export default DeadlinesSection;
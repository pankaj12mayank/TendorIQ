'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { 
  CheckCircle,
  Clock,
  AlertTriangle,
  Users,
  Calendar,
  FileText,
  ArrowRight
} from 'lucide-react';
import { ReviewSession } from '../types';
import { useReviewStore } from '../store';
import { STATUS_COLORS, PRIORITY_COLORS } from '../constants';
import { cn } from '@/lib/utils';

interface ReviewSummaryProps {
  className?: string;
}

export function ReviewSummary({ className }: ReviewSummaryProps) {
  const { session } = useReviewStore();

  if (!session) return null;

  const workflow = session.workflow;
  const totalSections = session.sectionStatuses.length;
  const approvedSections = session.sectionStatuses.filter(s => s.approvalStatus === 'approved').length;
  const pendingSections = session.sectionStatuses.filter(s => s.approvalStatus === 'pending').length;
  const needsRevisionSections = session.sectionStatuses.filter(s => s.approvalStatus === 'needs_revision').length;

  const daysRemaining = workflow.deadline
    ? Math.ceil((new Date(workflow.deadline).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
    : 0;

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <div className={cn('space-y-6', className)}>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Status</CardTitle>
            <Badge className={STATUS_COLORS[workflow.status].split(' ')[0]} variant="secondary">
              {workflow.status.replace('_', ' ')}
            </Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">{workflow.status.replace('_', ' ')}</div>
            <p className="text-xs text-muted-foreground">ID: {workflow.id}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Priority</CardTitle>
            <Badge className={PRIORITY_COLORS[workflow.priority]}>{workflow.priority}</Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">{workflow.priority}</div>
            <p className="text-xs text-muted-foreground">Current priority level</p>
          </CardContent>
        </Card>

        <Card className={daysRemaining <= 3 ? 'border-red-200 bg-red-50' : ''}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Deadline</CardTitle>
            <Calendar className={cn('h-4 w-4', daysRemaining <= 3 ? 'text-red-600' : 'text-muted-foreground')} />
          </CardHeader>
          <CardContent>
            <div className={cn('text-2xl font-bold', daysRemaining <= 3 && 'text-red-600')}>
              {daysRemaining} days
            </div>
            <p className="text-xs text-muted-foreground">
              {workflow.deadline && formatDate(workflow.deadline)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Reviewers</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{session.reviewers.length}</div>
            <p className="text-xs text-muted-foreground">Active reviewers</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Approved</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">{approvedSections}</div>
            <Progress value={(approvedSections / totalSections) * 100} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Clock className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-yellow-600">{pendingSections}</div>
            <Progress value={(pendingSections / totalSections) * 100} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Needs Revision</CardTitle>
            <AlertTriangle className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-600">{needsRevisionSections}</div>
            <Progress value={(needsRevisionSections / totalSections) * 100} className="mt-2" />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Approval Workflow</CardTitle>
          <CardDescription>Multi-step review and approval process</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            {workflow.steps.map((step, idx) => (
              <React.Fragment key={step.id}>
                <div className="flex flex-col items-center">
                  <div className={cn(
                    'w-10 h-10 rounded-full flex items-center justify-center mb-2',
                    step.status === 'completed' && 'bg-green-100 text-green-600',
                    step.status === 'in_progress' && 'bg-blue-100 text-blue-600',
                    step.status === 'pending' && 'bg-gray-100 text-gray-400'
                  )}>
                    {step.status === 'completed' ? (
                      <CheckCircle className="w-5 h-5" />
                    ) : (
                      <span className="text-sm font-bold">{idx + 1}</span>
                    )}
                  </div>
                  <span className="text-sm font-medium text-center">{step.name}</span>
                  <span className="text-xs text-muted-foreground capitalize">{step.role}</span>
                  {step.completedAt && (
                    <span className="text-xs text-green-600 mt-1">Completed</span>
                  )}
                </div>
                {idx < workflow.steps.length - 1 && (
                  <ArrowRight className={cn(
                    'w-5 h-5 mx-2',
                    step.status === 'completed' ? 'text-green-400' : 'text-gray-300'
                  )} />
                )}
              </React.Fragment>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Section Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
            {session.sectionStatuses.map((status) => (
              <div key={status.section} className="p-3 rounded-lg border bg-card">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium capitalize">{status.section.replace('_', ' ')}</span>
                  <Badge 
                    className={cn(
                      'text-xs',
                      status.approvalStatus === 'approved' && 'bg-green-100 text-green-800',
                      status.approvalStatus === 'pending' && 'bg-yellow-100 text-yellow-800',
                      status.approvalStatus === 'needs_revision' && 'bg-orange-100 text-orange-800'
                    )}
                  >
                    {status.approvalStatus.replace('_', ' ')}
                  </Badge>
                </div>
                <div className="text-xs text-muted-foreground">
                  {status.editCount > 0 && (
                    <span>{status.editCount} edits</span>
                  )}
                  {status.lastEditedBy && (
                    <span> by {status.lastEditedBy}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default ReviewSummary;
'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { 
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  ArrowRight,
  Send,
  RotateCcw
} from 'lucide-react';
import { ApprovalAction, ReviewSection } from '../types';
import { useApprovalWorkflow } from '@/hooks/use-review';
import { useReviewStore } from '../store';
import { cn } from '@/lib/utils';

interface ApprovalWorkflowProps {
  tenderId?: string;
  onApprove?: (comments?: string) => void;
  onReject?: (comments?: string) => void;
  onRequestChanges?: (sections: string[], comments: string) => void;
  className?: string;
}

export function ApprovalWorkflow({
  tenderId,
  onApprove,
  onReject,
  onRequestChanges,
  className,
}: ApprovalWorkflowProps) {
  const session = useReviewStore((s) => s.session);
  const { isLoading, submitApproval, requestChanges } = useApprovalWorkflow(tenderId);
  const [comments, setComments] = useState('');
  const [selectedSections, setSelectedSections] = useState<ReviewSection[]>([]);

  if (!session) return null;

  const workflow = session.workflow;
  const currentStep = workflow.steps.find(s => s.status === 'in_progress');

  const handleApprove = async () => {
    await submitApproval('approve', comments);
    onApprove?.(comments);
    setComments('');
  };

  const handleReject = async () => {
    await submitApproval('reject', comments);
    onReject?.(comments);
    setComments('');
  };

  const handleRequestChanges = async () => {
    await requestChanges(selectedSections, comments);
    onRequestChanges?.(selectedSections, comments);
    setComments('');
    setSelectedSections([]);
  };

  const toggleSection = (section: ReviewSection) => {
    setSelectedSections(prev =>
      prev.includes(section)
        ? prev.filter(s => s !== section)
        : [...prev, section]
    );
  };

  return (
    <Card className={cn(className)}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CheckCircle className="w-5 h-5" />
          Approval Workflow
        </CardTitle>
        <CardDescription>
          Current step: {currentStep?.name || 'Unknown'}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <label className="text-sm font-medium">Add Comments (Optional)</label>
          <Textarea
            placeholder="Enter your comments or feedback..."
            value={comments}
            onChange={(e) => setComments(e.target.value)}
            className="min-h-[100px]"
          />
        </div>

        <div className="space-y-3">
          <label className="text-sm font-medium">Select sections for changes (if any)</label>
          <div className="grid gap-2 md:grid-cols-2">
            {session.sectionStatuses.map((status) => (
              <div key={status.section} className="flex items-center gap-2 p-2 rounded-lg border">
                <Checkbox
                  id={`section-${status.section}`}
                  checked={selectedSections.includes(status.section as ReviewSection)}
                  onCheckedChange={() => toggleSection(status.section as ReviewSection)}
                />
                <label
                  htmlFor={`section-${status.section}`}
                  className="text-sm capitalize cursor-pointer flex-1"
                >
                  {status.section.replace('_', ' ')}
                </label>
                <Badge variant="outline" className="text-xs">
                  {status.approvalStatus}
                </Badge>
              </div>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <Button
            onClick={handleApprove}
            disabled={isLoading}
            className="w-full"
          >
            <CheckCircle className="w-4 h-4 mr-2" />
            Approve
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>

          <div className="grid grid-cols-2 gap-2">
            <Button
              variant="outline"
              onClick={handleRequestChanges}
              disabled={isLoading}
            >
              <AlertTriangle className="w-4 h-4 mr-2" />
              Request Changes
            </Button>
            <Button
              variant="destructive"
              onClick={handleReject}
              disabled={isLoading}
            >
              <XCircle className="w-4 h-4 mr-2" />
              Reject
            </Button>
          </div>
        </div>

        <div className="pt-4 border-t">
          <h4 className="text-sm font-medium mb-2">Workflow Progress</h4>
          <div className="space-y-2">
            {workflow.steps.map((step, idx) => (
              <div key={step.id} className="flex items-center gap-3">
                <div className={cn(
                  'w-8 h-8 rounded-full flex items-center justify-center text-sm',
                  step.status === 'completed' && 'bg-green-100 text-green-600',
                  step.status === 'in_progress' && 'bg-blue-100 text-blue-600',
                  step.status === 'pending' && 'bg-gray-100 text-gray-400'
                )}>
                  {step.status === 'completed' ? (
                    <CheckCircle className="w-4 h-4" />
                  ) : (
                    idx + 1
                  )}
                </div>
                <div className="flex-1">
                  <span className="text-sm font-medium">{step.name}</span>
                  {step.approver && (
                    <span className="text-xs text-muted-foreground ml-2">
                      - {step.approver.name}
                    </span>
                  )}
                </div>
                <Badge variant="outline" className="text-xs capitalize">
                  {step.status.replace('_', ' ')}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default ApprovalWorkflow;
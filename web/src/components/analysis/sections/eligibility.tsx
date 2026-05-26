'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { CheckCircle, XCircle, HelpCircle, Edit3, Save, X } from 'lucide-react';
import { EligibilityData } from '../types';
import { useAnalysisStore, getConfidenceColor, getStatusColor } from '../store';
import { cn } from '@/lib/utils';

interface EligibilitySectionProps {
  data: EligibilityData;
  isEditing?: boolean;
}

export function EligibilitySection({ data, isEditing = false }: EligibilitySectionProps) {
  const metCount = data.criteria.filter(c => c.isMet === true).length;
  const notMetCount = data.criteria.filter(c => c.isMet === false).length;
  const unknownCount = data.criteria.filter(c => c.isMet === null).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Eligibility Criteria</h2>
          <p className="text-muted-foreground">Assessment of compliance with tender requirements</p>
        </div>
        {!isEditing && (
          <Button variant="outline" size="sm">
            <Edit3 className="w-4 h-4 mr-2" />
            Edit
          </Button>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overall Score</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{data.overallScore}%</div>
            <Progress value={data.overallScore} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Criteria Met</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">{metCount}</div>
            <p className="text-xs text-muted-foreground">Fully compliant</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Not Met</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-red-600">{notMetCount}</div>
            <p className="text-xs text-muted-foreground">Requires attention</p>
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
          <CardTitle>Criteria Assessment</CardTitle>
          <CardDescription>{data.summary}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {data.criteria.map((criterion) => (
              <div
                key={criterion.id}
                className="flex items-start gap-4 p-4 rounded-lg border bg-card"
              >
                <div className={cn(
                  'w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0',
                  criterion.isMet === true && 'bg-green-100',
                  criterion.isMet === false && 'bg-red-100',
                  criterion.isMet === null && 'bg-gray-100'
                )}>
                  {criterion.isMet === true && <CheckCircle className="w-5 h-5 text-green-600" />}
                  {criterion.isMet === false && <XCircle className="w-5 h-5 text-red-600" />}
                  {criterion.isMet === null && <HelpCircle className="w-5 h-5 text-gray-600" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-medium">{criterion.criterion}</h4>
                    <Badge className={cn(
                      'text-xs',
                      criterion.isMet === true && 'bg-green-100 text-green-800',
                      criterion.isMet === false && 'bg-red-100 text-red-800',
                      criterion.isMet === null && 'bg-gray-100 text-gray-800'
                    )}>
                      {criterion.isMet === true && 'Met'}
                      {criterion.isMet === false && 'Not Met'}
                      {criterion.isMet === null && 'Unknown'}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mb-2">{criterion.requirement}</p>
                  {criterion.notes && (
                    <p className="text-sm text-muted-foreground italic">Note: {criterion.notes}</p>
                  )}
                  <div className="mt-2 flex items-center gap-4">
                    <span className="text-xs text-muted-foreground">
                      Confidence: {criterion.confidence}%
                    </span>
                    <Progress value={criterion.confidence} className="w-20 h-2" />
                  </div>
                </div>
              </div>
            ))}
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

export default EligibilitySection;
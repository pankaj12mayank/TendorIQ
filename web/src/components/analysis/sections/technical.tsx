'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { CheckCircle, XCircle, HelpCircle, Edit3, Save, X, Cpu } from 'lucide-react';
import { TechnicalData } from '../types';
import { useAnalysisStore, getConfidenceColor } from '../store';
import { cn } from '@/lib/utils';

interface TechnicalSectionProps {
  data: TechnicalData;
  isEditing?: boolean;
}

export function TechnicalSection({ data, isEditing = false }: TechnicalSectionProps) {
  const compliantCount = data.requirements.filter(r => r.isCompliant === true).length;
  const nonCompliantCount = data.requirements.filter(r => r.isCompliant === false).length;
  const pendingCount = data.requirements.filter(r => r.isCompliant === null).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-purple-100 rounded-lg">
            <Cpu className="w-6 h-6 text-purple-600" />
          </div>
          <div>
            <h2 className="text-2xl font-bold">Technical Requirements</h2>
            <p className="text-muted-foreground">Technical compliance assessment</p>
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
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Compliance Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{data.complianceRate}%</div>
            <Progress value={data.complianceRate} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Requirements Met</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">{compliantCount}</div>
            <p className="text-xs text-muted-foreground">Fully compliant</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Non-Compliant</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-red-600">{nonCompliantCount}</div>
            <p className="text-xs text-muted-foreground">Requires action</p>
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
          <CardTitle>Requirement Analysis</CardTitle>
          <CardDescription>{data.summary}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {data.requirements.map((req) => (
              <div
                key={req.id}
                className="flex items-center gap-4 p-4 rounded-lg border bg-card"
              >
                <div className={cn(
                  'w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0',
                  req.isCompliant === true && 'bg-green-100',
                  req.isCompliant === false && 'bg-red-100',
                  req.isCompliant === null && 'bg-yellow-100'
                )}>
                  {req.isCompliant === true && <CheckCircle className="w-5 h-5 text-green-600" />}
                  {req.isCompliant === false && <XCircle className="w-5 h-5 text-red-600" />}
                  {req.isCompliant === null && <HelpCircle className="w-5 h-5 text-yellow-600" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="font-medium">{req.name}</h4>
                    <Badge variant="outline" className="ml-2">
                      Weight: {req.weight}%
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mb-2">{req.specification}</p>
                  {req.notes && (
                    <p className="text-sm text-muted-foreground italic">Note: {req.notes}</p>
                  )}
                </div>
                <div className="text-right">
                  <Badge className={cn(
                    'text-xs',
                    req.isCompliant === true && 'bg-green-100 text-green-800',
                    req.isCompliant === false && 'bg-red-100 text-red-800',
                    req.isCompliant === null && 'bg-yellow-100 text-yellow-800'
                  )}>
                    {req.isCompliant === true && 'Compliant'}
                    {req.isCompliant === false && 'Non-Compliant'}
                    {req.isCompliant === null && 'Needs Review'}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Compliance Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{compliantCount}</div>
              <div className="text-sm text-muted-foreground">Fully Met</div>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">{pendingCount}</div>
              <div className="text-sm text-muted-foreground">Needs Review</div>
            </div>
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <div className="text-2xl font-bold text-red-600">{nonCompliantCount}</div>
              <div className="text-sm text-muted-foreground">Not Met</div>
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

export default TechnicalSection;
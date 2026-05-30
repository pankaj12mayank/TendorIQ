'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { FileText, Edit3, Save, X, CheckCircle, XCircle, Clock, Upload } from 'lucide-react';
import { MandatoryDocsData, DocumentRequirement } from '../types';
import { useAnalysisStore, getConfidenceColor } from '../store';
import { cn } from '@/lib/utils';

interface MandatoryDocsSectionProps {
  data: MandatoryDocsData;
  isEditing?: boolean;
  onEdit?: () => void;
  onSave?: () => void;
}

const STATUS_ICONS = {
  submitted: CheckCircle,
  pending: Clock,
  missing: XCircle,
};

const STATUS_COLORS = {
  submitted: 'text-green-600 bg-green-100',
  pending: 'text-yellow-600 bg-yellow-100',
  missing: 'text-red-600 bg-red-100',
};

export function MandatoryDocsSection({ data, isEditing = false, onEdit, onSave }: MandatoryDocsSectionProps) {
  const submittedCount = data.documents.filter(d => d.isSubmitted === true).length;
  const pendingCount = data.documents.filter(d => d.isSubmitted === null).length;
  const missingCount = data.documents.filter(d => d.isSubmitted === false).length;

  const getDocumentStatus = (doc: DocumentRequirement): 'submitted' | 'pending' | 'missing' => {
    if (doc.isSubmitted === true) return 'submitted';
    if (doc.isSubmitted === false) return 'missing';
    return 'pending';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-indigo-100 rounded-lg">
            <FileText className="w-6 h-6 text-indigo-600" />
          </div>
          <div>
            <h2 className="text-2xl font-bold">Mandatory Documents</h2>
            <p className="text-muted-foreground">Required documentation checklist</p>
          </div>
        </div>
        {!isEditing && (
          <Button variant="outline" size="sm" onClick={onEdit}>
            <Edit3 className="w-4 h-4 mr-2" />
            Edit
          </Button>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completion</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{data.overallCompletion}%</div>
            <Progress value={data.overallCompletion} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Submitted</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">{submittedCount}</div>
            <p className="text-xs text-muted-foreground">Ready for review</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-yellow-600">{pendingCount}</div>
            <p className="text-xs text-muted-foreground">Need to prepare</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Missing</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-red-600">{missingCount}</div>
            <p className="text-xs text-muted-foreground">Must submit</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Document Checklist</CardTitle>
          <CardDescription>{data.summary}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {data.documents.map((doc) => {
              const status = getDocumentStatus(doc);
              const StatusIcon = STATUS_ICONS[status];

              return (
                <div
                  key={doc.id}
                  className="flex items-center gap-4 p-4 rounded-lg border bg-card"
                >
                  <div className={cn('p-2 rounded-lg flex-shrink-0', STATUS_COLORS[status])}>
                    <StatusIcon className="w-5 h-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium">{doc.name}</h4>
                      {doc.isRequired && (
                        <Badge variant="destructive" className="text-xs">Required</Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">{doc.description}</p>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span className="px-2 py-1 bg-muted rounded">Type: {doc.documentType}</span>
                      {doc.pageLimit && (
                        <span className="px-2 py-1 bg-muted rounded">Limit: {doc.pageLimit} pages</span>
                      )}
                      {doc.notes && (
                        <span className="text-yellow-600">{doc.notes}</span>
                      )}
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    {doc.submittedDate && (
                      <p className="text-xs text-muted-foreground mb-1">
                        Submitted: {doc.submittedDate}
                      </p>
                    )}
                    <Badge className={cn(
                      'text-xs',
                      status === 'submitted' && 'bg-green-100 text-green-800',
                      status === 'pending' && 'bg-yellow-100 text-yellow-800',
                      status === 'missing' && 'bg-red-100 text-red-800'
                    )}>
                      {status === 'submitted' && 'Submitted'}
                      {status === 'pending' && 'Pending'}
                      {status === 'missing' && 'Missing'}
                    </Badge>
                  </div>
                  {status !== 'submitted' && (
                    <Button size="sm" variant="outline">
                      <Upload className="w-4 h-4 mr-2" />
                      Upload
                    </Button>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Document Status Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center gap-4 py-8">
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-2">
                <span className="text-2xl font-bold text-green-600">{submittedCount}</span>
              </div>
              <p className="text-sm text-muted-foreground">Submitted</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-yellow-100 flex items-center justify-center mx-auto mb-2">
                <span className="text-2xl font-bold text-yellow-600">{pendingCount}</span>
              </div>
              <p className="text-sm text-muted-foreground">Pending</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-2">
                <span className="text-2xl font-bold text-red-600">{missingCount}</span>
              </div>
              <p className="text-sm text-muted-foreground">Missing</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {isEditing && (
        <div className="flex justify-end gap-2 pt-4 border-t">
          <Button variant="outline" onClick={onSave}>
            <X className="w-4 h-4 mr-2" />
            Cancel
          </Button>
          <Button onClick={onSave}>
            <Save className="w-4 h-4 mr-2" />
            Save Changes
          </Button>
        </div>
      )}
    </div>
  );
}

export default MandatoryDocsSection;
'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { AlertTriangle, Edit3, Save, X, TrendingUp, Shield, AlertCircle } from 'lucide-react';
import { RisksData, RiskItem } from '../types';
import { useAnalysisStore, getConfidenceColor, getRiskColor } from '../store';
import { cn } from '@/lib/utils';

interface RisksSectionProps {
  data: RisksData;
  isEditing?: boolean;
  onEdit?: () => void;
  onSave?: () => void;
}

export function RisksSection({ data, isEditing = false, onEdit, onSave }: RisksSectionProps) {
  const severityCounts = {
    critical: data.risks.filter(r => r.severity === 'critical').length,
    high: data.risks.filter(r => r.severity === 'high').length,
    medium: data.risks.filter(r => r.severity === 'medium').length,
    low: data.risks.filter(r => r.severity === 'low').length,
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <AlertCircle className="w-5 h-5" />;
      case 'high':
        return <AlertTriangle className="w-5 h-5" />;
      default:
        return <Shield className="w-5 h-5" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-orange-100 rounded-lg">
            <AlertTriangle className="w-6 h-6 text-orange-600" />
          </div>
          <div>
            <h2 className="text-2xl font-bold">Risk Assessment</h2>
            <p className="text-muted-foreground">Identified risks and mitigation strategies</p>
          </div>
        </div>
        {!isEditing && (
          <Button variant="outline" size="sm" onClick={onEdit}>
            <Edit3 className="w-4 h-4 mr-2" />
            Edit
          </Button>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card className="bg-red-50 border-red-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-red-800">Critical</CardTitle>
            <AlertCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-red-600">{severityCounts.critical}</div>
          </CardContent>
        </Card>

        <Card className="bg-orange-50 border-orange-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-orange-800">High</CardTitle>
            <AlertTriangle className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-600">{severityCounts.high}</div>
          </CardContent>
        </Card>

        <Card className="bg-yellow-50 border-yellow-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-yellow-800">Medium</CardTitle>
            <Shield className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-yellow-600">{severityCounts.medium}</div>
          </CardContent>
        </Card>

        <Card className="bg-green-50 border-green-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-green-800">Low</CardTitle>
            <Shield className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">{severityCounts.low}</div>
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
          <CardTitle>Risk Register</CardTitle>
          <CardDescription>{data.summary}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {data.risks.map((risk) => (
              <div
                key={risk.id}
                className="p-4 rounded-lg border bg-card"
              >
                <div className="flex items-start gap-4">
                  <div className={cn(
                    'p-3 rounded-lg flex-shrink-0',
                    risk.severity === 'critical' && 'bg-red-100 text-red-600',
                    risk.severity === 'high' && 'bg-orange-100 text-orange-600',
                    risk.severity === 'medium' && 'bg-yellow-100 text-yellow-600',
                    risk.severity === 'low' && 'bg-green-100 text-green-600'
                  )}>
                    {getSeverityIcon(risk.severity)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <h4 className="font-semibold">{risk.title}</h4>
                      <Badge className={cn('text-xs', getRiskColor(risk.severity))}>
                        {risk.severity}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mb-3">{risk.description}</p>
                    <div className="grid gap-3 md:grid-cols-3">
                      <div>
                        <span className="text-xs text-muted-foreground uppercase tracking-wide">Probability</span>
                        <div className="flex items-center gap-2 mt-1">
                          <Progress value={risk.probability} className="flex-1 h-2" />
                          <span className="text-sm font-medium">{risk.probability}%</span>
                        </div>
                      </div>
                      <div>
                        <span className="text-xs text-muted-foreground uppercase tracking-wide">Impact</span>
                        <p className="text-sm font-medium mt-1">{risk.impact}</p>
                      </div>
                      {risk.owner && (
                        <div>
                          <span className="text-xs text-muted-foreground uppercase tracking-wide">Owner</span>
                          <p className="text-sm font-medium mt-1">{risk.owner}</p>
                        </div>
                      )}
                    </div>
                    <div className="mt-3 p-3 bg-muted rounded-lg">
                      <span className="text-xs text-muted-foreground uppercase tracking-wide">Mitigation</span>
                      <p className="text-sm mt-1">{risk.mitigation}</p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
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

export default RisksSection;
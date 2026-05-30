'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { DollarSign, Edit3, Save, X, Percent, Calendar } from 'lucide-react';
import { FinancialData } from '../types';
import { useAnalysisStore, getConfidenceColor } from '../store';
import { cn } from '@/lib/utils';

interface FinancialSectionProps {
  data: FinancialData;
  isEditing?: boolean;
  onEdit?: () => void;
  onSave?: () => void;
}

export function FinancialSection({ data, isEditing = false, onEdit, onSave }: FinancialSectionProps) {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: data.currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const totalCost = data.breakdown.reduce((sum, item) => sum + item.total, 0) || 1;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-green-100 rounded-lg">
            <DollarSign className="w-6 h-6 text-green-600" />
          </div>
          <div>
            <h2 className="text-2xl font-bold">Financial Analysis</h2>
            <p className="text-muted-foreground">Cost breakdown and payment terms</p>
          </div>
        </div>
        {!isEditing && (
          <Button variant="outline" size="sm" onClick={onEdit}>
            <Edit3 className="w-4 h-4 mr-2" />
            Edit
          </Button>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Total Project Value</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-green-600 mb-4">{data.totalValue}</div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Percent className="w-4 h-4" />
              <span>AI Confidence: {data.overallConfidence.value}%</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Payment Terms</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{data.paymentTerms}</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Cost Breakdown</CardTitle>
          <CardDescription>{data.summary}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 font-medium">Item</th>
                  <th className="text-right py-3 px-4 font-medium">Unit Cost</th>
                  <th className="text-right py-3 px-4 font-medium">Qty/Unit</th>
                  <th className="text-right py-3 px-4 font-medium">Total</th>
                  <th className="text-right py-3 px-4 font-medium">%</th>
                </tr>
              </thead>
              <tbody>
                {data.breakdown.map((item) => (
                  <tr key={item.item} className="border-b last:border-0">
                    <td className="py-3 px-4">{item.item}</td>
                    <td className="py-3 px-4 text-right">{formatCurrency(item.amount)}</td>
                    <td className="py-3 px-4 text-right">{item.quantity} {item.unit}</td>
                    <td className="py-3 px-4 text-right font-medium">{formatCurrency(item.total)}</td>
                    <td className="py-3 px-4 text-right text-muted-foreground">
                      {((item.total / totalCost) * 100).toFixed(1)}%
                    </td>
                  </tr>
                ))}
                <tr className="bg-muted/50 font-semibold">
                  <td className="py-3 px-4" colSpan={3}>Total</td>
                  <td className="py-3 px-4 text-right">{formatCurrency(totalCost)}</td>
                  <td className="py-3 px-4 text-right">100%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Advance Payments</CardTitle>
          <CardDescription>Available advance payment options</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            {data.advances.map((advance, idx) => (
              <div key={idx} className="p-4 bg-green-50 rounded-lg border border-green-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium">{advance.type}</span>
                  <span className="text-2xl font-bold text-green-600">{advance.percentage}%</span>
                </div>
                <p className="text-sm text-muted-foreground">
                  Advance amount: {formatCurrency(totalCost * advance.percentage / 100)}
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Cost Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {data.breakdown.map((item) => {
              const percentage = (item.total / totalCost) * 100;
              return (
                <div key={item.item} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span>{item.item}</span>
                    <span className="text-muted-foreground">{percentage.toFixed(1)}%</span>
                  </div>
                  <div className="h-3 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-green-500 to-green-600 rounded-full transition-all"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
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

export default FinancialSection;
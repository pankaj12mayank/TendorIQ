'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  BarChart2,
  TrendingUp,
  TrendingDown,
  Users,
  FileText,
  Cpu,
  DollarSign,
  Calendar,
  Download,
  RefreshCw,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import { UsageMetric } from '../types';
import { MOCK_USAGE_METRICS, ANALYTICS_CARDS } from '../constants';
import { cn } from '@/lib/utils';

interface SparklineProps {
  data: number[];
  color?: string;
  height?: number;
}

function Sparkline({ data, color = '#3b82f6', height = 40 }: SparklineProps) {
  if (!data.length) return null;
  
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  
  const points = data.map((value, i) => {
    const x = (i / (data.length - 1)) * 100;
    const y = height - ((value - min) / range) * height;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg viewBox={`0 0 100 ${height}`} className="w-full" style={{ height }}>
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function UsageAnalytics() {
  const [timeRange, setTimeRange] = useState('7d');
  const [metrics] = useState(ANALYTICS_CARDS);
  const usageData = MOCK_USAGE_METRICS;

  const totalApiCalls = usageData.reduce((sum, d) => sum + d.apiCalls, 0);
  const totalDocuments = usageData.reduce((sum, d) => sum + d.documentsProcessed, 0);
  const totalTokens = usageData.reduce((sum, d) => sum + d.tokensUsed, 0);
  const totalCost = usageData.reduce((sum, d) => sum + d.cost, 0);

  const sparklineApiCalls = usageData.map((d) => d.apiCalls);
  const sparklineDocuments = usageData.map((d) => d.documentsProcessed);
  const sparklineCost = usageData.map((d) => d.cost);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Usage Analytics</h2>
          <p className="text-muted-foreground">Track usage metrics and trends</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-[150px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
              <SelectItem value="90d">Last 90 days</SelectItem>
              <SelectItem value="1y">Last year</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Button variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric, idx) => (
          <Card key={idx}>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-muted-foreground">{metric.title}</span>
                {metric.trend === 'up' ? (
                  <TrendingUp className="w-4 h-4 text-green-600" />
                ) : metric.trend === 'down' ? (
                  <TrendingDown className="w-4 h-4 text-red-600" />
                ) : (
                  <BarChart2 className="w-4 h-4 text-gray-400" />
                )}
              </div>
              <div className="text-3xl font-bold mb-2">{metric.value}</div>
              <div className="flex items-center gap-1">
                {metric.changeType === 'increase' && metric.trend === 'up' && (
                  <ArrowUpRight className="w-4 h-4 text-green-600" />
                )}
                {metric.changeType === 'decrease' && metric.trend === 'down' && (
                  <ArrowDownRight className="w-4 h-4 text-red-600" />
                )}
                <span className={cn(
                  'text-sm font-medium',
                  metric.changeType === 'increase' ? 'text-green-600' : 'text-red-600'
                )}>
                  {metric.change}%
                </span>
                <span className="text-sm text-muted-foreground">vs last period</span>
              </div>
              {metric.sparklineData && (
                <div className="mt-4">
                  <Sparkline data={metric.sparklineData} />
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>API Calls Trend</CardTitle>
            <CardDescription>Daily API call volume over time</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Sparkline data={sparklineApiCalls} height={100} />
              <div className="grid grid-cols-3 gap-4 pt-4 border-t">
                <div>
                  <p className="text-sm text-muted-foreground">Total</p>
                  <p className="text-2xl font-bold">{totalApiCalls.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Average/Day</p>
                  <p className="text-2xl font-bold">{Math.round(totalApiCalls / usageData.length).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Peak</p>
                  <p className="text-2xl font-bold">{Math.max(...sparklineApiCalls).toLocaleString()}</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Cost Trend</CardTitle>
            <CardDescription>Daily AI cost over time</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Sparkline data={sparklineCost} color="#22c55e" height={100} />
              <div className="grid grid-cols-3 gap-4 pt-4 border-t">
                <div>
                  <p className="text-sm text-muted-foreground">Total Cost</p>
                  <p className="text-2xl font-bold">${totalCost.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Avg/Day</p>
                  <p className="text-2xl font-bold">${(totalCost / usageData.length).toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Cost/Doc</p>
                  <p className="text-2xl font-bold">${(totalCost / totalDocuments).toFixed(2)}</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Detailed Usage Table</CardTitle>
          <CardDescription>Day-by-day breakdown of usage metrics</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 font-medium">Date</th>
                  <th className="text-right py-3 px-4 font-medium">API Calls</th>
                  <th className="text-right py-3 px-4 font-medium">Documents</th>
                  <th className="text-right py-3 px-4 font-medium">Tokens Used</th>
                  <th className="text-right py-3 px-4 font-medium">Cost</th>
                </tr>
              </thead>
              <tbody>
                {usageData.map((day) => (
                  <tr key={day.date} className="border-b last:border-0">
                    <td className="py-3 px-4">{new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</td>
                    <td className="py-3 px-4 text-right font-mono">{day.apiCalls.toLocaleString()}</td>
                    <td className="py-3 px-4 text-right font-mono">{day.documentsProcessed}</td>
                    <td className="py-3 px-4 text-right font-mono">{day.tokensUsed.toLocaleString()}</td>
                    <td className="py-3 px-4 text-right font-mono">${day.cost.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="bg-muted/50 font-semibold">
                  <td className="py-3 px-4">Total</td>
                  <td className="py-3 px-4 text-right">{totalApiCalls.toLocaleString()}</td>
                  <td className="py-3 px-4 text-right">{totalDocuments}</td>
                  <td className="py-3 px-4 text-right">{totalTokens.toLocaleString()}</td>
                  <td className="py-3 px-4 text-right">${totalCost.toFixed(2)}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default UsageAnalytics;
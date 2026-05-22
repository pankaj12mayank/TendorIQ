'use client';

import React, { useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useAnalysisApi } from '@/hooks/use-analysis';
import { 
  AnalysisContent, 
  AnalysisTabs,
  AnalysisProgress 
} from '@/components/analysis';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { 
  Download, 
  RefreshCw, 
  Share2, 
  Printer,
  FileText,
  ChevronLeft,
  MoreHorizontal
} from 'lucide-react';
import { cn } from '@/lib/utils';

export default function TenderAnalysisPage() {
  const searchParams = useSearchParams();
  const tenderId = searchParams.get('tenderId') ?? undefined;
  const { analysis, isLoading, isError, error, exportAnalysis, refetch } = useAnalysisApi(tenderId);
  const [exportFormat, setExportFormat] = useState<'pdf' | 'docx' | 'json' | 'csv'>('pdf');

  const handleExport = async () => {
    await exportAnalysis(exportFormat);
  };

  if (!tenderId) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-16 text-center">
        <p className="text-muted-foreground">Select a tender to view analysis.</p>
        <Button asChild variant="outline">
          <Link href="/dashboard/tenders">Back to tenders</Link>
        </Button>
      </div>
    );
  }

  if (isError && !analysis) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-16 text-center">
        <p className="text-destructive">{error ?? 'Failed to load analysis'}</p>
        <Button variant="outline" onClick={() => refetch()}>
          Retry
        </Button>
      </div>
    );
  }

  if (isLoading && !analysis) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-200px)]">
        <div className="text-center space-y-4">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-muted-foreground">Loading analysis...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/dashboard/tenders" className="p-2 hover:bg-muted rounded-lg">
            <ChevronLeft className="w-5 h-5" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-3xl font-bold tracking-tight">Tender Analysis</h1>
              {analysis?.status === 'completed' && (
                <Badge className="bg-green-100 text-green-800">Complete</Badge>
              )}
            </div>
            <p className="text-muted-foreground">
              {analysis?.tenderId} - AI-powered comprehensive analysis
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => refetch()}>
            <RefreshCw className={cn('w-4 h-4 mr-2', isLoading && 'animate-spin')} />
            Refresh
          </Button>
          <Button variant="outline">
            <Share2 className="w-4 h-4 mr-2" />
            Share
          </Button>
          <Button variant="outline">
            <Printer className="w-4 h-4 mr-2" />
            Print
          </Button>
          <div className="flex items-center gap-2">
            <select
              className="h-10 px-3 rounded-md border bg-background text-sm"
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value as typeof exportFormat)}
            >
              <option value="pdf">PDF</option>
              <option value="docx">DOCX</option>
              <option value="json">JSON</option>
              <option value="csv">CSV</option>
            </select>
            <Button onClick={handleExport}>
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </div>
      </div>

      <Card>
        <CardHeader className="pb-0">
          <div className="flex items-center justify-between">
            <CardTitle>Analysis Sections</CardTitle>
            <div className="text-sm text-muted-foreground">
              Last updated: {analysis?.updatedAt && new Date(analysis.updatedAt).toLocaleString()}
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          <AnalysisContent />
        </CardContent>
      </Card>
    </div>
  );
}
'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useState } from 'react';
import { FileDown, FileText, Loader2 } from 'lucide-react';
import { appToast } from '@/lib/app-toast';
import { AnalysisContent } from '@/components/analysis';
import { PageHeader } from '@/components/design-system/page-header';
import { Button } from '@/components/ui/button';
import { ROUTES } from '@/lib/routes';
import { useAnalysisApi } from '@/hooks/use-analysis';
import { LoadingState } from '@/components/ui/loading-state';
import { PremiumErrorState } from '@/components/design-system/empty-state';

export default function AnalysisPage() {
  const params = useSearchParams();
  const tenderId = params.get('tenderId') ?? undefined;
  const { isLoading, error, exportAnalysis } = useAnalysisApi(tenderId);
  const [exporting, setExporting] = useState(false);

  return (
    <div className="space-y-8">
      <PageHeader
        title="Analysis"
        description={
          tenderId
            ? `AI-powered tender analysis for this document.`
            : 'AI-powered tender analysis — open from Upload or pick a tender below.'
        }
        actions={
          tenderId ? (
            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                disabled={exporting || isLoading}
                onClick={async () => {
                  setExporting(true);
                  try {
                    await exportAnalysis();
                    appToast.success('Analysis PDF downloaded.');
                  } catch (err) {
                    appToast.error(err instanceof Error ? err.message : 'Export failed');
                  } finally {
                    setExporting(false);
                  }
                }}
              >
                {exporting ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <FileDown className="mr-2 h-4 w-4" />
                )}
                Export PDF
              </Button>
              <Button variant="outline" asChild>
                <Link href={`${ROUTES.proposal}?tenderId=${tenderId}`}>
                  <FileText className="mr-2 h-4 w-4" />
                  Create proposal
                </Link>
              </Button>
            </div>
          ) : undefined
        }
      />
      {isLoading && <LoadingState message="Loading analysis..." />}
      {error && (
        <PremiumErrorState
          title="Analysis unavailable"
          description={typeof error === 'string' ? error : 'Could not load analysis'}
        />
      )}
      {!isLoading && !error && <AnalysisContent />}
      {!tenderId && !isLoading && (
        <p className="text-sm text-muted-foreground">
          Open this page with <code>?tenderId=</code> after uploading documents.
        </p>
      )}
    </div>
  );
}

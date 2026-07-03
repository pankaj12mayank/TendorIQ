'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useState } from 'react';
import { FileDown, FileText, Loader2 } from 'lucide-react';
import { appToast } from '@/lib/app-toast';
import { SubscriptionGate } from '@/components/billing/subscription-gate';
import { AnalysisContent } from '@/components/analysis';
import { Button } from '@/components/ui/button';
import { ROUTES } from '@/lib/routes';
import { useAnalysisApi } from '@/hooks/use-analysis';
import { LoadingState } from '@/components/ui/loading-state';
import { PremiumErrorState } from '@/components/design-system/empty-state';

export default function AnalysisPage() {
  const params = useSearchParams();
  const tenderId = params.get('tenderId') ?? undefined;
  const { isLoading, error, refetch, exportAnalysis } = useAnalysisApi(tenderId);
  const [exporting, setExporting] = useState(false);

  return (
    <SubscriptionGate>
    <div className="w-full space-y-6">
      {tenderId ? (
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <p className="text-sm text-muted-foreground">AI-powered tender analysis for this document.</p>
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
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">
          Open this page with <code>?tenderId=</code> after uploading documents.
        </p>
      )}
      {isLoading && <LoadingState message="Loading analysis..." />}
      {error && (
        <PremiumErrorState
          title="Analysis unavailable"
          description={typeof error === 'string' ? error : 'Could not load analysis'}
          onRetry={() => refetch()}
        />
      )}
      {!isLoading && !error && <AnalysisContent />}
    </div>
    </SubscriptionGate>
  );
}

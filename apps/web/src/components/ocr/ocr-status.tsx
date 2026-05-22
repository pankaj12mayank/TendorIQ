'use client';

import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { FileText, RefreshCw, AlertTriangle, CheckCircle2, Loader2, Eye } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useOCRApi, OCRStatus } from '@/hooks/use-ocr';
interface OCRStatusCardProps {
  documentId: string;
  documentName: string;
  onViewResult?: (result: OCRStatus['result']) => void;
  autoPoll?: boolean;
  className?: string;
}

const statusConfig: Record<string, { label: string; className: string; icon: React.ElementType }> = {
  uploaded: { label: 'Pending OCR', className: 'border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-950', icon: FileText },
  processing: { label: 'Processing', className: 'border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-950', icon: Loader2 },
  retrying: { label: 'Retrying', className: 'border-orange-200 bg-orange-50 dark:border-orange-800 dark:bg-orange-950', icon: RefreshCw },
  completed: { label: 'Completed', className: 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950', icon: CheckCircle2 },
  failed: { label: 'Failed', className: 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950', icon: AlertTriangle },
  needs_review: { label: 'Needs Review', className: 'border-purple-200 bg-purple-50 dark:border-purple-800 dark:bg-purple-950', icon: AlertTriangle },
};

export function OCRStatusCard({
  documentId,
  documentName,
  onViewResult,
  autoPoll = false,
  className,
}: OCRStatusCardProps) {
  const { getStatus, pollStatus, retryOCR, loading } = useOCRApi();
  const [status, setStatus] = useState<OCRStatus | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  useEffect(() => {
    fetchStatus();
  }, [documentId]);

  useEffect(() => {
    if (!autoPoll || !status) return;

    const needsPolling = ['uploaded', 'processing', 'retrying'].includes(status.ocr_status);
    if (!needsPolling) return;

    setIsPolling(true);

    pollStatus(documentId, 60, 5000)
      .then((newStatus) => {
        setStatus(newStatus);
        if (newStatus.ocr_status === 'completed') {
          toast.success('OCR processing completed', { description: documentName });
        } else if (newStatus.ocr_status === 'failed') {
          toast.error('OCR processing failed', { description: documentName });
        }
      })
      .catch(() => {
        toast.error('OCR polling failed');
      })
      .finally(() => {
        setIsPolling(false);
      });

  }, [status, autoPoll, documentId]);

  const fetchStatus = async () => {
    try {
      const s = await getStatus(documentId);
      setStatus(s);
    } catch {
      toast.error('Failed to fetch OCR status');
    }
  };

  const handleRetry = async () => {
    try {
      await retryOCR([documentId]);
      toast.success('OCR retry queued');
      fetchStatus();
    } catch (err) {
      toast.error('Failed to retry OCR');
    }
  };

  const statusKey = status?.ocr_status || 'uploaded';
  const config = (statusConfig[statusKey] || statusConfig.uploaded)!;
  const Icon = config.icon;

  return (
    <Card className={cn('overflow-hidden', className)}>
      <div className={cn('border-l-4', config.className.replace('bg-', 'border-l-').replace('-50', '').replace('-950', ''))}>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Icon className={cn('h-4 w-4', status?.ocr_status === 'processing' && 'animate-spin')} />
              <CardTitle className="text-sm font-medium">{config.label}</CardTitle>
            </div>
            {isPolling && (
              <span className="text-xs text-muted-foreground">Polling...</span>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm font-medium truncate">{documentName}</p>

          {status?.result && (
            <div className="space-y-2 rounded bg-muted/50 p-3 text-xs">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Confidence:</span>
                <span className="font-medium">
                  {(status.result.confidence * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Words:</span>
                <span className="font-medium">{status.result.word_count.toLocaleString()}</span>
              </div>
              {status.result.is_low_quality && (
                <div className="flex items-center gap-1 text-yellow-600">
                  <AlertTriangle className="h-3 w-3" />
                  <span>Low quality detected</span>
                </div>
              )}
            </div>
          )}

          <div className="flex gap-2">
            {status?.result && onViewResult && (
              <Button size="sm" variant="outline" onClick={() => onViewResult(status.result)} className="flex-1 gap-1">
                <Eye className="h-3 w-3" />
                View
              </Button>
            )}

            {(status?.ocr_status === 'failed' || status?.ocr_status === 'needs_review') && (
              <Button
                size="sm"
                variant="outline"
                onClick={handleRetry}
                disabled={loading}
                className="flex-1 gap-1"
              >
                <RefreshCw className={cn('h-3 w-3', loading && 'animate-spin')} />
                Retry
              </Button>
            )}
          </div>
        </CardContent>
      </div>
    </Card>
  );
}

export function OCRResultViewer({
  result,
  onClose,
}: {
  result: OCRStatus['result'];
  onClose: () => void;
}) {
  if (!result) return null;

  const qualityColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="max-h-[90vh] w-full max-w-4xl overflow-hidden rounded-lg bg-background shadow-xl">
        <div className="flex items-center justify-between border-b p-4">
          <div>
            <h2 className="text-lg font-semibold">OCR Result</h2>
            <p className="text-sm text-muted-foreground">
              Confidence: {(result.confidence * 100).toFixed(1)}% | Words: {result.word_count.toLocaleString()}
            </p>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>Close</Button>
        </div>

        <div className="grid gap-4 p-4 lg:grid-cols-4">
          <div className="space-y-3 lg:col-span-1">
            <h3 className="text-sm font-medium">Quality Scores</h3>
            <div className="space-y-2 rounded-lg bg-muted/50 p-3">
              <div>
                <div className="flex justify-between text-xs">
                  <span>Blur</span>
                  <span className={qualityColor(result.quality_scores.blur)}>
                    {(result.quality_scores.blur * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full bg-primary transition-all"
                    style={{ width: `${result.quality_scores.blur * 100}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs">
                  <span>Brightness</span>
                  <span className={qualityColor(result.quality_scores.brightness)}>
                    {(result.quality_scores.brightness * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full bg-primary transition-all"
                    style={{ width: `${result.quality_scores.brightness * 100}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs">
                  <span>Contrast</span>
                  <span className={qualityColor(result.quality_scores.contrast)}>
                    {(result.quality_scores.contrast * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full bg-primary transition-all"
                    style={{ width: `${result.quality_scores.contrast * 100}%` }}
                  />
                </div>
              </div>
            </div>

            {result.is_low_quality && (
              <div className="flex items-center gap-2 rounded-lg border border-yellow-200 bg-yellow-50 p-2 text-xs text-yellow-700 dark:border-yellow-800 dark:bg-yellow-950 dark:text-yellow-300">
                <AlertTriangle className="h-4 w-4" />
                Low quality input - some text may be inaccurate
              </div>
            )}
          </div>

          <div className="lg:col-span-3">
            <h3 className="mb-2 text-sm font-medium">Extracted Text</h3>
            <div className="max-h-[50vh] overflow-auto rounded-lg border bg-muted/30 p-4">
              <pre className="whitespace-pre-wrap text-sm">{result.text || 'No text extracted'}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
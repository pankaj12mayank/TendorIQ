'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { Upload, ExternalLink } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { FileUploader } from '@/components/upload/file-uploader';
import { AiModelPicker } from '@/components/upload/ai-model-picker';
import { useDashboardStore } from '@/stores/dashboard-store';
import { useDocumentProcessing } from '@/hooks/use-document-processing';
import { loadAiSelection, type AiSelection } from '@/hooks/use-ai-catalog';
import { mergePrefsWithLocal, useAiPreferences } from '@/hooks/use-ai-preferences';
import type { UploadResult } from '@/hooks/use-file-upload';
import { toast } from 'sonner';

function ProcessingBanner({ documentId }: { documentId: string }) {
  const { status, isProcessing, isComplete, isFailed, tenderId, retryAnalysis } =
    useDocumentProcessing(documentId);

  if (!status) return null;

  return (
    <div className="rounded-md border p-3 text-sm space-y-2">
      <p>
        <span className="font-medium">Status:</span>{' '}
        {status.processing_status}
        {isProcessing && ' — AI analysis running…'}
      </p>
      {isFailed && (
        <>
          <p className="text-destructive text-xs">{status.processing_error}</p>
          <button
            type="button"
            className="text-xs underline"
            onClick={() => void retryAnalysis()}
          >
            Retry analysis
          </button>
        </>
      )}
      {isComplete && tenderId && (
        <div className="flex flex-wrap gap-3">
          <Link
            href={`/dashboard/analysis?tenderId=${tenderId}`}
            className="inline-flex items-center gap-1 text-primary underline text-xs"
          >
            View analysis <ExternalLink className="h-3 w-3" />
          </Link>
          <Link
            href={`/dashboard/proposal?tenderId=${tenderId}`}
            className="inline-flex items-center gap-1 text-primary underline text-xs"
          >
            Create proposal <ExternalLink className="h-3 w-3" />
          </Link>
        </div>
      )}
    </div>
  );
}

export default function UploadPage() {
  const { data: savedPrefs } = useAiPreferences();
  const [aiSelection, setAiSelection] = useState<AiSelection>(() => loadAiSelection());

  useEffect(() => {
    if (savedPrefs) setAiSelection(mergePrefsWithLocal(savedPrefs));
  }, [savedPrefs]);
  const [lastDocumentId, setLastDocumentId] = useState<string | null>(null);
  const addActivity = useDashboardStore((state) => state.addActivity);

  const handleUploadComplete = (results: UploadResult[]) => {
    const ok = results.filter((r) => r.success && r.document_id);
    if (ok.length === 0) {
      toast.error('Upload failed');
      return;
    }
    const last = ok[ok.length - 1];
    if (last.document_id) setLastDocumentId(last.document_id);

    toast.success(
      `${ok.length} file(s) uploaded — AI analysis started (${aiSelection.provider}/${aiSelection.model})`
    );
    addActivity({
      id: `activity-${Date.now()}`,
      type: 'complete',
      title: `${ok.length} documents uploaded`,
      description: 'AI analysis queued automatically after upload',
      time: 'Just now',
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Upload Documents</h1>
        <p className="text-muted-foreground">Upload and process your tender documents.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="w-5 h-5" />
                Document Upload
              </CardTitle>
              <CardDescription>
                PDF or Word documents only (DOC/DOCX), up to 25MB each.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <AiModelPicker value={aiSelection} onChange={setAiSelection} />
              <FileUploader
                aiSelection={aiSelection}
                onUploadComplete={handleUploadComplete}
                maxFiles={10}
                category="documents"
              />
              {lastDocumentId && <ProcessingBanner documentId={lastDocumentId} />}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Upload Guidelines</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div>
                <h4 className="font-medium mb-1">Supported Files</h4>
                <p className="text-muted-foreground">PDF, DOC, DOCX (max 25MB each)</p>
              </div>
              <div>
                <h4 className="font-medium mb-1">Best Practices</h4>
                <ul className="text-muted-foreground list-disc list-inside space-y-1">
                  <li>Use clear, readable documents</li>
                  <li>Ensure PDFs are text-based (not scanned)</li>
                  <li>Organize multi-page documents</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium mb-1">Processing</h4>
                <p className="text-muted-foreground">
                  After upload, TenderIQ extracts text and runs your chosen AI model (OpenAI,
                  Anthropic, Gemini, or local Ollama).
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
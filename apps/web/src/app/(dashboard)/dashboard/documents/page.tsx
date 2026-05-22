'use client';

import { useState, useEffect } from 'react';
import { Upload, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { FileUploader } from '@/components/upload/file-uploader';
import { DocumentStats } from '@/components/documents/document-stats';
import { DocumentTable } from '@/components/documents/document-table';
import { useDocumentsApi } from '@/hooks/use-documents';
import { useDocumentStore } from '@/stores/document-store';
import { toast } from 'sonner';

export default function DocumentsPage() {
  const [showUpload, setShowUpload] = useState(false);
  const { retryDocuments, fetchDocuments, stats } = useDocumentsApi();

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleRetryFailed = async () => {
    const failed = useDocumentStore
      .getState()
      .documents.filter((d) => d.processing_status === 'failed')
      .map((d) => d.id);
    if (failed.length === 0) {
      useDocumentStore.getState().setFilters({ status: ['failed'] });
      await fetchDocuments();
      const refreshed = useDocumentStore
        .getState()
        .documents.filter((d) => d.processing_status === 'failed')
        .map((d) => d.id);
      if (refreshed.length === 0) {
        toast.message('No failed documents to retry');
        return;
      }
      await retryDocuments(refreshed);
      toast.success(`Retrying ${refreshed.length} documents`);
      return;
    }
    await retryDocuments(failed);
    toast.success(`Retrying ${failed.length} documents`);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Documents</h1>
          <p className="text-muted-foreground">Manage your documents and files</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={handleRetryFailed}
            className="gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Retry Failed
          </Button>
          <Button
            onClick={() => setShowUpload(!showUpload)}
            className="gap-2"
          >
            <Upload className="h-4 w-4" />
            Upload
          </Button>
        </div>
      </div>

      <DocumentStats />

      {showUpload && (
        <div className="rounded-lg border bg-card p-6">
          <h2 className="text-lg font-semibold mb-4">Upload Documents</h2>
          <FileUploader
            category="documents"
            onUploadComplete={(results) => {
              const successCount = results.filter((r) => r.success).length;
              if (successCount > 0) {
                toast.success(`${successCount} document(s) uploaded successfully`);
                fetchDocuments();
                setShowUpload(false);
              }
            }}
          />
        </div>
      )}

      <DocumentTable />
    </div>
  );
}
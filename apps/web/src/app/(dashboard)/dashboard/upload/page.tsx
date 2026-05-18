'use client';

import { Upload } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { UploadTracker } from '@/components/dashboard';
import { useDashboardStore } from '@/stores/dashboard-store';
import { useToastStore } from '@/stores/toast-store';

export default function UploadPage() {
  const addActivity = useDashboardStore((state) => state.addActivity);
  const addToast = useToastStore((state) => state.addToast);

  const handleUploadComplete = (results: unknown[]) => {
    addToast('success', 'Upload Complete', `${results.length} files processed successfully`);
    addActivity({
      id: `activity-${Date.now()}`,
      type: 'complete',
      title: `${results.length} documents uploaded`,
      description: 'Files have been processed and are ready for review',
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
                Drag and drop files or click to browse. Supported formats: PDF, DOC, DOCX, JPG, PNG
              </CardDescription>
            </CardHeader>
            <CardContent>
              <UploadTracker
                onUploadComplete={handleUploadComplete}
                maxFiles={10}
                maxSizeMB={10}
              />
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
                <p className="text-muted-foreground">PDF, DOC, DOCX, JPG, PNG (max 10MB each)</p>
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
                  Documents are automatically analyzed for key information extraction.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
'use client';

import React, { useState, useCallback } from 'react';
import { toast } from 'sonner';
import { FileText, File, Download, Clock, FileSpreadsheet, Code, Trash2, RefreshCw } from 'lucide-react';
import { ExportJob, getExportHistory, downloadExport, getExportFilename, formatFileSize, ExportFormat } from '@/lib/export';
import { cn } from '@/lib/utils';

interface ExportHistoryProps {
  limit?: number;
  onExportClick?: (job: ExportJob) => void;
  className?: string;
}

const FORMAT_ICONS: Record<string, React.ReactNode> = {
  pdf: <FileText className="w-4 h-4" />,
  docx: <File className="w-4 h-4" />,
  csv: <FileSpreadsheet className="w-4 h-4" />,
  json: <Code className="w-4 h-4" />,
  markdown: <FileText className="w-4 h-4" />,
  html: <File className="w-4 h-4" />,
};

const STATUS_STYLES = {
  pending: { bg: 'bg-gray-100', text: 'text-gray-600', label: 'Pending' },
  processing: { bg: 'bg-blue-100', text: 'text-blue-600', label: 'Processing' },
  completed: { bg: 'bg-green-100', text: 'text-green-600', label: 'Completed' },
  failed: { bg: 'bg-red-100', text: 'text-red-600', label: 'Failed' },
};

export function ExportHistory({ limit = 50, onExportClick, className }: ExportHistoryProps) {
  const [history, setHistory] = useState<ExportJob[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const loadHistory = useCallback(async () => {
    setIsLoading(true);
    try {
      const result = await getExportHistory(limit);
      setHistory(result.exports);
    } catch (error) {
      toast.error('Failed to load export history');
    } finally {
      setIsLoading(false);
    }
  }, [limit]);

  React.useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const handleDownload = useCallback(async (job: ExportJob) => {
    setDownloadingId(job.job_id);
    try {
      const blob = await downloadExport(job.export_id);
      const filename = getExportFilename(job, job.format as ExportFormat);
      
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);
    } catch {
      toast.error('Download failed');
    } finally {
      setDownloadingId(null);
    }
  }, []);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className={cn('bg-white rounded-lg border border-gray-200 shadow-sm', className)}>
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gray-100 rounded-lg">
            <Clock className="w-4 h-4 text-gray-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">Export History</h3>
            <p className="text-xs text-gray-500">{history.length} exports</p>
          </div>
        </div>
        <button
          onClick={loadHistory}
          disabled={isLoading}
          className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <RefreshCw className={cn('w-4 h-4', isLoading && 'animate-spin')} />
        </button>
      </div>

      <div className="divide-y max-h-96 overflow-y-auto">
        {history.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No exports yet</p>
          </div>
        ) : (
          history.map(job => {
            const status = STATUS_STYLES[job.status as keyof typeof STATUS_STYLES] || STATUS_STYLES.pending;
            return (
              <div key={job.job_id} className="p-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-center gap-4">
                  <div className={cn('p-2 rounded-lg', status.bg)}>
                    <span className={status.text}>
                      {FORMAT_ICONS[job.format] || <FileText className="w-4 h-4" />}
                    </span>
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm text-gray-900 uppercase">{job.format}</span>
                      <span className={cn('text-xs px-2 py-0.5 rounded-full', status.bg, status.text)}>
                        {status.label}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatDate(job.created_at)}
                      </span>
                      {job.file_size_bytes && (
                        <span>{formatFileSize(job.file_size_bytes)}</span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {job.status === 'completed' && (
                      <button
                        onClick={() => handleDownload(job)}
                        disabled={downloadingId === job.job_id}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50"
                        title="Download"
                      >
                        {downloadingId === job.job_id ? (
                          <RefreshCw className="w-4 h-4 animate-spin" />
                        ) : (
                          <Download className="w-4 h-4" />
                        )}
                      </button>
                    )}
                    {onExportClick && (
                      <button
                        onClick={() => onExportClick(job)}
                        className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors"
                        title="View Details"
                      >
                        <FileText className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

export default ExportHistory;
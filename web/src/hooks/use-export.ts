'use client';

import { useState, useCallback } from 'react';
import {
  createExport,
  exportEntity,
  downloadExport,
  getJobStatus,
  ExportFormat,
  ExportType,
  ExportJob,
} from '@/lib/export';

interface UseExportReturn {
  isExporting: boolean;
  lastExport: ExportJob | null;
  error: string | null;
  exportDocument: (type: ExportType, id: string, format?: ExportFormat) => Promise<ExportJob>;
  downloadLastExport: () => Promise<void>;
  clearError: () => void;
}

export function useExport(): UseExportReturn {
  const [isExporting, setIsExporting] = useState(false);
  const [lastExport, setLastExport] = useState<ExportJob | null>(null);
  const [error, setError] = useState<string | null>(null);

  const exportDocument = useCallback(async (
    type: ExportType,
    id: string,
    format: ExportFormat = 'pdf'
  ): Promise<ExportJob> => {
    setIsExporting(true);
    setError(null);

    try {
      const job = await exportEntity(type, id, format);
      setLastExport(job);
      return job;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Export failed';
      setError(message);
      throw err;
    } finally {
      setIsExporting(false);
    }
  }, []);

  const downloadLastExport = useCallback(async (): Promise<void> => {
    if (!lastExport?.export_id) return;

    setIsExporting(true);
    try {
      const blob = await downloadExport(lastExport.export_id);
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `tendoriq-export-${lastExport.export_id}.${lastExport.format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Download failed');
    } finally {
      setIsExporting(false);
    }
  }, [lastExport]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    isExporting,
    lastExport,
    error,
    exportDocument,
    downloadLastExport,
    clearError,
  };
}

interface UseBatchExportReturn {
  isExporting: boolean;
  results: ExportJob[];
  exportBatch: (items: Array<{ type: ExportType; id: string }>, format: ExportFormat) => Promise<ExportJob[]>;
  clearResults: () => void;
}

export function useBatchExport(): UseBatchExportReturn {
  const [isExporting, setIsExporting] = useState(false);
  const [results, setResults] = useState<ExportJob[]>([]);

  const exportBatch = useCallback(async (
    items: Array<{ type: ExportType; id: string }>,
    format: ExportFormat
  ): Promise<ExportJob[]> => {
    setIsExporting(true);

    try {
      const exports = items.map(item => ({
        export_type: item.type,
        format,
        source_id: item.id,
        source_type: item.type,
      }));

      const { batch_id, results: batchResults } = await import('@/lib/export').then(m => m.batchExport(exports));
      setResults(batchResults);
      return batchResults;
    } finally {
      setIsExporting(false);
    }
  }, []);

  const clearResults = useCallback(() => {
    setResults([]);
  }, []);

  return {
    isExporting,
    results,
    exportBatch,
    clearResults,
  };
}
'use client';

import React, { useState, useCallback } from 'react';
import { toast } from 'sonner';
import { CheckSquare, Loader, Download, FileText, File, FileSpreadsheet } from 'lucide-react';
import { ExportFormat, ExportRequest, ExportJob, batchExport, downloadExport, getExportFilename, formatFileSize } from '@/lib/export';
import { cn } from '@/lib/utils';

interface BatchExportItem {
  id: string;
  type: 'proposal' | 'checklist' | 'risk_analysis' | 'tender_document';
  title: string;
  selected: boolean;
}

interface BatchExportProps {
  items: BatchExportItem[];
  defaultFormat?: ExportFormat;
  onComplete?: (results: ExportJob[]) => void;
  className?: string;
}

const FORMAT_OPTIONS: Array<{ value: ExportFormat; label: string; icon: React.ReactNode }> = [
  { value: 'pdf', label: 'PDF', icon: <FileText className="w-4 h-4" /> },
  { value: 'docx', label: 'DOCX', icon: <File className="w-4 h-4" /> },
  { value: 'csv', label: 'CSV', icon: <FileSpreadsheet className="w-4 h-4" /> },
];

export function BatchExport({ items, defaultFormat = 'pdf', onComplete, className }: BatchExportProps) {
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>(defaultFormat);
  const [localItems, setLocalItems] = useState<BatchExportItem[]>(items);
  const [isExporting, setIsExporting] = useState(false);
  const [results, setResults] = useState<ExportJob[]>([]);
  const [currentDownload, setCurrentDownload] = useState<string | null>(null);

  const selectedCount = localItems.filter(i => i.selected).length;

  const toggleItem = useCallback((id: string) => {
    setLocalItems(prev => prev.map(item => 
      item.id === id ? { ...item, selected: !item.selected } : item
    ));
  }, []);

  const selectAll = useCallback(() => {
    const allSelected = localItems.every(i => i.selected);
    setLocalItems(prev => prev.map(item => ({ ...item, selected: !allSelected })));
  }, [localItems]);

  const handleBatchExport = useCallback(async () => {
    if (selectedCount === 0) return;
    
    setIsExporting(true);
    setResults([]);

    const exports: ExportRequest[] = localItems
      .filter(item => item.selected)
      .map(item => ({
        export_type: item.type,
        format: selectedFormat,
        source_id: item.id,
        source_type: item.type,
        title: item.title,
      }));

    try {
      const batchResult = await batchExport(exports);
      setResults(batchResult.results);
      
      for (const job of batchResult.results) {
        if (job.status === 'completed') {
          try {
            const blob = await downloadExport(job.export_id);
            const filename = getExportFilename(job, selectedFormat);
            
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(link.href);
            
            await new Promise(resolve => setTimeout(resolve, 500));
          } catch {
            toast.error(`Download failed for job ${job.job_id}`);
          }
        }
      }
      
      onComplete?.(batchResult.results);
    } catch {
      toast.error('Batch export failed');
    } finally {
      setIsExporting(false);
    }
  }, [localItems, selectedFormat, selectedCount, onComplete]);

  const successCount = results.filter(r => r.status === 'completed').length;
  const failedCount = results.filter(r => r.status === 'failed').length;

  return (
    <div className={cn('bg-white rounded-lg border border-gray-200 shadow-sm p-6', className)}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Download className="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">Batch Export</h3>
            <p className="text-sm text-gray-500">{selectedCount} items selected</p>
          </div>
        </div>
        
        <div className="flex gap-2">
          {FORMAT_OPTIONS.map(option => (
            <button
              key={option.value}
              onClick={() => setSelectedFormat(option.value)}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
                selectedFormat === option.value
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              )}
            >
              {option.icon}
              {option.label}
            </button>
          ))}
        </div>
      </div>

      <div className="border rounded-lg divide-y max-h-80 overflow-y-auto">
        <div className="p-3 bg-gray-50 flex items-center justify-between">
          <button
            onClick={selectAll}
            className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
          >
            <CheckSquare className="w-4 h-4" />
            {localItems.every(i => i.selected) ? 'Deselect All' : 'Select All'}
          </button>
          <span className="text-sm text-gray-500">{selectedCount} of {localItems.length} selected</span>
        </div>

        {localItems.map(item => (
          <div
            key={item.id}
            className="p-3 flex items-center gap-3 hover:bg-gray-50 cursor-pointer"
            onClick={() => toggleItem(item.id)}
          >
            <input
              type="checkbox"
              checked={item.selected}
              onChange={() => toggleItem(item.id)}
              className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <div className="flex-1">
              <div className="font-medium text-sm text-gray-900">{item.title}</div>
              <div className="text-xs text-gray-500 capitalize">{item.type.replace('_', ' ')}</div>
            </div>
          </div>
        ))}
      </div>

      {results.length > 0 && (
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-1.5 text-green-600">
              <CheckSquare className="w-4 h-4" />
              {successCount} successful
            </div>
            {failedCount > 0 && (
              <div className="flex items-center gap-1.5 text-red-600">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                {failedCount} failed
              </div>
            )}
          </div>
        </div>
      )}

      <button
        onClick={handleBatchExport}
        disabled={selectedCount === 0 || isExporting}
        className={cn(
          'mt-4 w-full px-4 py-2.5 text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors',
          'disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2'
        )}
      >
        {isExporting ? (
          <>
            <Loader className="w-4 h-4 animate-spin" />
            Exporting {selectedCount} documents...
          </>
        ) : (
          <>
            <Download className="w-4 h-4" />
            Export {selectedCount} Documents as {selectedFormat.toUpperCase()}
          </>
        )}
      </button>
    </div>
  );
}

export default BatchExport;
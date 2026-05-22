'use client';

import React, { useState, useCallback } from 'react';
import { toast } from 'sonner';
import { Download, ChevronDown, FileText, FileSpreadsheet, Code, File } from 'lucide-react';
import { ExportFormat, exportEntity, downloadExport, formatFileSize, triggerDownload, getExportFilename } from '@/lib/export';
import { cn } from '@/lib/utils';

interface ExportButtonProps {
  entityType: 'proposal' | 'checklist' | 'risk_analysis' | 'tender_document';
  entityId: string;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  className?: string;
}

const FORMAT_OPTIONS: Array<{ value: ExportFormat; label: string; icon: React.ReactNode }> = [
  { value: 'pdf', label: 'PDF Document', icon: <FileText className="w-4 h-4" /> },
  { value: 'docx', label: 'Word Document', icon: <File className="w-4 h-4" /> },
  { value: 'csv', label: 'CSV Spreadsheet', icon: <FileSpreadsheet className="w-4 h-4" /> },
  { value: 'json', label: 'JSON Data', icon: <Code className="w-4 h-4" /> },
  { value: 'markdown', label: 'Markdown', icon: <FileText className="w-4 h-4" /> },
];

const VARIANT_STYLES = {
  primary: 'bg-blue-600 text-white hover:bg-blue-700 border-blue-600',
  secondary: 'bg-gray-100 text-gray-700 hover:bg-gray-200 border-gray-300',
  outline: 'border border-gray-300 text-gray-700 hover:bg-gray-50',
  ghost: 'text-gray-600 hover:bg-gray-100 border-transparent',
};

const SIZE_STYLES = {
  sm: 'px-3 py-1.5 text-sm gap-1.5',
  md: 'px-4 py-2 text-sm gap-2',
  lg: 'px-5 py-2.5 text-base gap-2',
};

export function ExportButton({
  entityType,
  entityId,
  variant = 'primary',
  size = 'md',
  showIcon = true,
  className,
}: ExportButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [downloadedFormat, setDownloadedFormat] = useState<ExportFormat | null>(null);

  const handleExport = useCallback(async (format: ExportFormat) => {
    setIsLoading(true);
    setDownloadedFormat(format);
    setIsOpen(false);

    try {
      const job = await exportEntity(entityType, entityId, format);
      const blob = await downloadExport(job.export_id);
      const filename = getExportFilename(job, format);
      triggerDownload(blob, filename);
    } catch {
      toast.error('Export failed');
    } finally {
      setIsLoading(false);
      setDownloadedFormat(null);
    }
  }, [entityType, entityId]);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isLoading}
        className={cn(
          'inline-flex items-center justify-center rounded-md font-medium transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          VARIANT_STYLES[variant],
          SIZE_STYLES[size],
          className
        )}
      >
        {isLoading ? (
          <>
            <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span>Exporting {downloadedFormat?.toUpperCase()}...</span>
          </>
        ) : (
          <>
            {showIcon && <Download className="w-4 h-4" />}
            <span>Export</span>
            <ChevronDown className="w-3 h-3" />
          </>
        )}
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 mt-2 w-56 bg-white rounded-md shadow-lg border border-gray-200 py-1 z-20">
            {FORMAT_OPTIONS.map((option) => (
              <button
                key={option.value}
                onClick={() => handleExport(option.value)}
                className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-3"
              >
                {option.icon}
                <span>{option.label}</span>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

interface ExportDropdownProps {
  onExport: (format: ExportFormat) => void;
  disabled?: boolean;
  label?: string;
  className?: string;
}

export function ExportDropdown({ onExport, disabled, label = 'Export', className }: ExportDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className={cn('relative', className)}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
        className={cn(
          'inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md',
          'hover:bg-blue-700 transition-colors disabled:opacity-50',
          'focus:outline-none focus:ring-2 focus:ring-blue-500'
        )}
      >
        <Download className="w-4 h-4" />
        {label}
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          <div className="absolute top-full left-0 mt-1 w-48 bg-white rounded-md shadow-lg border border-gray-200 py-1 z-20">
            {FORMAT_OPTIONS.map((option) => (
              <button
                key={option.value}
                onClick={() => {
                  onExport(option.value);
                  setIsOpen(false);
                }}
                className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-3"
              >
                {option.icon}
                {option.label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default ExportButton;
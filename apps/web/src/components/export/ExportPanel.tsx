'use client';

import React, { useState, useCallback } from 'react';
import { Download, FileText, File, Code, FileSpreadsheet, Shield, Settings, Layers, Clock } from 'lucide-react';
import { ExportFormat, ExportTemplate, WATERMARK_PRESETS, exportEntity, downloadExport, getExportFilename, formatFileSize, batchExport, ExportRequest } from '@/lib/export';
import { cn } from '@/lib/utils';

interface ExportPanelProps {
  entityType: 'proposal' | 'checklist' | 'risk_analysis' | 'tender_document' | 'report';
  entityId: string;
  entityTitle?: string;
  onClose?: () => void;
  className?: string;
}

const FORMAT_ICONS = {
  pdf: <FileText className="w-5 h-5" />,
  docx: <File className="w-5 h-5" />,
  html: <Code className="w-5 h-5" />,
  markdown: <FileText className="w-5 h-5" />,
  json: <Code className="w-5 h-5" />,
  csv: <FileSpreadsheet className="w-5 h-5" />,
};

const FORMAT_DESCRIPTIONS = {
  pdf: 'Best for printing and sharing',
  docx: 'Editable in Microsoft Word',
  html: 'Viewable in any browser',
  markdown: 'Version control friendly',
  json: 'For integrations and APIs',
  csv: 'For spreadsheets and data analysis',
};

export function ExportPanel({ entityType, entityId, entityTitle, onClose, className }: ExportPanelProps) {
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('pdf');
  const [selectedTemplate, setSelectedTemplate] = useState<string>('default');
  const [includeWatermark, setIncludeWatermark] = useState(false);
  const [selectedWatermark, setSelectedWatermark] = useState<string>('');
  const [includeTimestamp, setIncludeTimestamp] = useState(true);
  const [includeLogo, setIncludeLogo] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const [exportResult, setExportResult] = useState<{ success: boolean; message: string; size?: number } | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleExport = useCallback(async () => {
    setIsExporting(true);
    setExportResult(null);

    try {
      const job = await exportEntity(entityType, entityId, selectedFormat, selectedTemplate !== 'default' ? selectedTemplate : undefined);
      const blob = await downloadExport(job.export_id);
      const filename = getExportFilename(job, selectedFormat);
      
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);

      setExportResult({
        success: true,
        message: 'Export completed successfully',
        size: job.file_size_bytes,
      });
    } catch (error) {
      setExportResult({
        success: false,
        message: error instanceof Error ? error.message : 'Export failed',
      });
    } finally {
      setIsExporting(false);
    }
  }, [entityType, entityId, selectedFormat, selectedTemplate]);

  const templates: ExportTemplate[] = [
    { template_id: 'default', name: 'Standard Report', primary_color: '#3182ce', secondary_color: '#718096', accent_color: '#2c5282', font_family: 'Segoe UI', show_page_numbers: true, show_timestamp: true, show_watermark: false },
    { template_id: 'branded', name: 'Branded Document', primary_color: '#1a365d', secondary_color: '#4a5568', accent_color: '#3182ce', font_family: 'Segoe UI', show_page_numbers: true, show_timestamp: true, show_watermark: false },
    { template_id: 'confidential', name: 'Confidential', primary_color: '#c53030', secondary_color: '#718096', accent_color: '#742a2a', font_family: 'Segoe UI', show_page_numbers: true, show_timestamp: true, show_watermark: true },
  ];

  return (
    <div className={cn('bg-white rounded-lg border border-gray-200 shadow-lg p-6', className)}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Download className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">Export Document</h3>
            {entityTitle && <p className="text-sm text-gray-500">{entityTitle}</p>}
          </div>
        </div>
        {onClose && (
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      <div className="space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Select Format</label>
          <div className="grid grid-cols-3 gap-2">
            {(Object.keys(FORMAT_ICONS) as ExportFormat[]).map((format) => (
              <button
                key={format}
                onClick={() => setSelectedFormat(format)}
                className={cn(
                  'p-3 rounded-lg border-2 text-left transition-all',
                  selectedFormat === format
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                )}
              >
                <div className={cn('mb-1', selectedFormat === format ? 'text-blue-600' : 'text-gray-600')}>
                  {FORMAT_ICONS[format]}
                </div>
                <div className="font-medium text-sm text-gray-900 uppercase">{format}</div>
                <div className="text-xs text-gray-500 mt-0.5">{FORMAT_DESCRIPTIONS[format]}</div>
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <Layers className="w-4 h-4 inline mr-1" />
            Template
          </label>
          <div className="flex gap-2">
            {templates.map((template) => (
              <button
                key={template.template_id}
                onClick={() => setSelectedTemplate(template.template_id)}
                className={cn(
                  'flex-1 p-3 rounded-lg border-2 text-left transition-all',
                  selectedTemplate === template.template_id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                )}
              >
                <div className="w-4 h-4 rounded-full mb-2" style={{ backgroundColor: template.primary_color }} />
                <div className="font-medium text-sm text-gray-900">{template.name}</div>
                <div className="text-xs text-gray-500 flex items-center gap-1 mt-1">
                  {template.show_page_numbers && <span className="text-gray-400">#</span>}
                  {template.show_timestamp && <Clock className="w-3 h-3" />}
                  {template.show_watermark && <Shield className="w-3 h-3 text-red-500" />}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div>
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
          >
            <Settings className="w-4 h-4" />
            Advanced Options
            <svg className={cn('w-4 h-4 transition-transform', showAdvanced && 'rotate-180')} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {showAdvanced && (
            <div className="mt-4 space-y-4 p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-sm text-gray-900">Include Logo</div>
                  <div className="text-xs text-gray-500">Add company logo to header</div>
                </div>
                <button
                  onClick={() => setIncludeLogo(!includeLogo)}
                  className={cn('relative w-11 h-6 rounded-full transition-colors', includeLogo ? 'bg-blue-600' : 'bg-gray-300')}
                >
                  <span className={cn('absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform', includeLogo && 'translate-x-5')} />
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-sm text-gray-900">Include Timestamp</div>
                  <div className="text-xs text-gray-500">Add generation date/time</div>
                </div>
                <button
                  onClick={() => setIncludeTimestamp(!includeTimestamp)}
                  className={cn('relative w-11 h-6 rounded-full transition-colors', includeTimestamp ? 'bg-blue-600' : 'bg-gray-300')}
                >
                  <span className={cn('absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform', includeTimestamp && 'translate-x-5')} />
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-sm text-gray-900">Watermark</div>
                  <div className="text-xs text-gray-500">Add confidential stamp</div>
                </div>
                <button
                  onClick={() => setIncludeWatermark(!includeWatermark)}
                  className={cn('relative w-11 h-6 rounded-full transition-colors', includeWatermark ? 'bg-blue-600' : 'bg-gray-300')}
                >
                  <span className={cn('absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform', includeWatermark && 'translate-x-5')} />
                </button>
              </div>

              {includeWatermark && (
                <div className="pt-2">
                  <label className="block text-xs font-medium text-gray-700 mb-2">Watermark Style</label>
                  <div className="grid grid-cols-2 gap-2">
                    {WATERMARK_PRESETS.map((preset) => (
                      <button
                        key={preset.id}
                        onClick={() => setSelectedWatermark(preset.id)}
                        className={cn(
                          'p-2 rounded-lg border text-left text-xs transition-all',
                          selectedWatermark === preset.id
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        )}
                      >
                        <div className="font-medium" style={{ color: preset.watermark.color }}>{preset.watermark.text}</div>
                        <div className="text-gray-500 text-[10px]">{preset.name}</div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {exportResult && (
        <div className={cn('mt-4 p-3 rounded-lg', exportResult.success ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800')}>
          <div className="flex items-center gap-2">
            {exportResult.success ? (
              <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              <svg className="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            )}
            <span>{exportResult.message}</span>
            {exportResult.size && <span className="text-sm opacity-75">({formatFileSize(exportResult.size)})</span>}
          </div>
        </div>
      )}

      <div className="mt-6 flex gap-3">
        {onClose && (
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            Cancel
          </button>
        )}
        <button
          onClick={handleExport}
          disabled={isExporting}
          className={cn(
            'flex-1 px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors',
            'disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2'
          )}
        >
          {isExporting ? (
            <>
              <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Exporting...
            </>
          ) : (
            <>
              <Download className="w-4 h-4" />
              Export as {selectedFormat.toUpperCase()}
            </>
          )}
        </button>
      </div>
    </div>
  );
}

export default ExportPanel;
import { api } from './api-client';
import { authenticatedFetch } from './api-fetch';
import {
  entityExportPath,
  parseExportHistory,
  parseExportJob,
} from './export-api';

/** Lite MVP: only PDF is supported for user-facing export. */
export type ExportFormat = 'pdf';
export type LegacyExportFormat = 'pdf' | 'docx' | 'html' | 'markdown' | 'json' | 'csv';
export type ExportType = 'proposal' | 'checklist' | 'risk_analysis' | 'tender_document' | 'report';

export interface ExportRequest {
  export_type: ExportType;
  format: ExportFormat;
  source_id: string;
  source_type: string;
  title?: string;
  template_id?: string;
  include_watermark?: boolean;
  include_logo?: boolean;
  include_timestamp?: boolean;
}

export interface ExportJob {
  job_id: string;
  export_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  format: ExportFormat;
  download_url?: string;
  file_size_bytes?: number;
  created_at: string;
}

export interface ExportTemplate {
  template_id: string;
  name: string;
  logo_url?: string;
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  font_family: string;
  show_page_numbers: boolean;
  show_timestamp: boolean;
  show_watermark: boolean;
  watermark?: {
    text: string;
    opacity: number;
    font_size: number;
    color: string;
    position: string;
  };
}

export interface WatermarkPreset {
  id: string;
  name: string;
  watermark: {
    text: string;
    opacity: number;
    font_size: number;
    color: string;
    position: string;
  };
}

export const EXPORT_FORMATS: Record<ExportFormat, { label: string; extension: string; mimeType: string }> = {
  pdf: { label: 'PDF Document', extension: '.pdf', mimeType: 'application/pdf' },
};

export { downloadTenderAnalysisPdf, fetchExportConfig, LITE_EXPORT_FORMAT } from './export-lite';

export const WATERMARK_PRESETS: WatermarkPreset[] = [
  { id: 'confidential', name: 'Confidential', watermark: { text: 'CONFIDENTIAL', opacity: 0.15, font_size: 36, color: '#c53030', position: 'diagonal' } },
  { id: 'draft', name: 'Draft', watermark: { text: 'DRAFT', opacity: 0.10, font_size: 30, color: '#718096', position: 'diagonal' } },
  { id: 'internal', name: 'Internal Use Only', watermark: { text: 'INTERNAL USE ONLY', opacity: 0.12, font_size: 24, color: '#2c5282', position: 'tile' } },
  { id: 'review', name: 'For Review', watermark: { text: 'FOR REVIEW', opacity: 0.10, font_size: 28, color: '#805ad5', position: 'center' } },
];

export async function createExport(request: ExportRequest): Promise<ExportJob> {
  const res = await api.post<unknown>('/api/v1/exports/export', request);
  return parseExportJob(res);
}

export async function exportEntity(
  entityType: ExportType,
  entityId: string,
  format: ExportFormat = 'pdf',
  templateId?: string
): Promise<ExportJob> {
  const params: Record<string, string | number | boolean> = { format };
  if (templateId) params.template_id = templateId;
  const res = await api.post<unknown>(entityExportPath(entityType, entityId), undefined, { params });
  return parseExportJob(res);
}

export async function exportTenderReport(
  tenderId: string,
  format: ExportFormat = 'pdf',
  templateId?: string
): Promise<ExportJob> {
  if (format !== 'pdf') {
    throw new Error('TenderIQ Lite supports PDF export only');
  }
  return exportEntity('report', tenderId, 'pdf', templateId);
}

export async function downloadExport(exportId: string): Promise<Blob> {
  const response = await authenticatedFetch(`/api/v1/exports/${exportId}/download`);

  if (!response.ok) {
    throw new Error('Download failed');
  }

  return response.blob();
}

export async function getJobStatus(jobId: string): Promise<ExportJob> {
  const res = await api.get<unknown>(`/api/v1/exports/jobs/${jobId}`);
  return parseExportJob(res);
}

export async function getExportTemplates(): Promise<ExportTemplate[]> {
  return api.get<ExportTemplate[]>('/api/v1/exports/templates');
}

export async function createExportTemplate(template: Partial<ExportTemplate>): Promise<ExportTemplate> {
  return api.post<ExportTemplate>('/api/v1/exports/templates', template);
}

export async function getExportFormats(): Promise<{ formats: Array<{ id: string; name: string; description: string }> }> {
  return api.get('/api/v1/exports/formats');
}

export async function batchExport(exports: ExportRequest[]): Promise<{ batch_id: string; results: ExportJob[] }> {
  const res = await api.post<{ batch_id: string; results: unknown[] }>('/api/v1/exports/batch', exports);
  return {
    batch_id: res.batch_id,
    results: (res.results ?? []).map(parseExportJob),
  };
}

export async function getExportHistory(limit = 50): Promise<{ exports: ExportJob[]; total: number }> {
  const res = await api.get<unknown>('/api/v1/exports/history', { params: { limit } });
  return parseExportHistory(res);
}

export function getExportFilename(job: ExportJob, format: ExportFormat): string {
  const extension = EXPORT_FORMATS[format].extension;
  const timestamp = new Date().toISOString().split('T')[0];
  return `tendoriq-export-${timestamp}${extension}`;
}

export function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function formatFileSize(bytes: number | undefined): string {
  if (!bytes) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  let size = bytes;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  return `${size.toFixed(1)} ${units[unitIndex]}`;
}

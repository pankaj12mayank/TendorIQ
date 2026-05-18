const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export type ExportFormat = 'pdf' | 'docx' | 'html' | 'markdown' | 'json' | 'csv';
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
  docx: { label: 'Word Document', extension: '.docx', mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' },
  html: { label: 'HTML Page', extension: '.html', mimeType: 'text/html' },
  markdown: { label: 'Markdown', extension: '.md', mimeType: 'text/markdown' },
  json: { label: 'JSON Data', extension: '.json', mimeType: 'application/json' },
  csv: { label: 'CSV Spreadsheet', extension: '.csv', mimeType: 'text/csv' },
};

export const WATERMARK_PRESETS: WatermarkPreset[] = [
  { id: 'confidential', name: 'Confidential', watermark: { text: 'CONFIDENTIAL', opacity: 0.15, font_size: 36, color: '#c53030', position: 'diagonal' } },
  { id: 'draft', name: 'Draft', watermark: { text: 'DRAFT', opacity: 0.10, font_size: 30, color: '#718096', position: 'diagonal' } },
  { id: 'internal', name: 'Internal Use Only', watermark: { text: 'INTERNAL USE ONLY', opacity: 0.12, font_size: 24, color: '#2c5282', position: 'tile' } },
  { id: 'review', name: 'For Review', watermark: { text: 'FOR REVIEW', opacity: 0.10, font_size: 28, color: '#805ad5', position: 'center' } },
];

export async function createExport(request: ExportRequest): Promise<ExportJob> {
  const response = await fetch(`${API_URL}/api/v1/exports/export`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Export creation failed');
  }

  return response.json();
}

export async function exportEntity(
  entityType: ExportType,
  entityId: string,
  format: ExportFormat = 'pdf',
  templateId?: string
): Promise<ExportJob> {
  const endpoint = `/api/v1/exports/export/${entityType}/${entityId}`;
  const params = new URLSearchParams({ format });
  if (templateId) params.append('template_id', templateId);

  const response = await fetch(`${API_URL}${endpoint}?${params}`, {
    method: 'POST',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Export failed');
  }

  return response.json();
}

export async function downloadExport(exportId: string): Promise<Blob> {
  const response = await fetch(`${API_URL}/api/v1/exports/${exportId}/download`);

  if (!response.ok) {
    throw new Error('Download failed');
  }

  return response.blob();
}

export async function getJobStatus(jobId: string): Promise<ExportJob> {
  const response = await fetch(`${API_URL}/api/v1/exports/jobs/${jobId}`);

  if (!response.ok) {
    throw new Error('Failed to get job status');
  }

  return response.json();
}

export async function getExportTemplates(): Promise<ExportTemplate[]> {
  const response = await fetch(`${API_URL}/api/v1/exports/templates`);

  if (!response.ok) {
    throw new Error('Failed to fetch templates');
  }

  return response.json();
}

export async function createExportTemplate(template: Partial<ExportTemplate>): Promise<ExportTemplate> {
  const response = await fetch(`${API_URL}/api/v1/exports/templates`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(template),
  });

  if (!response.ok) {
    throw new Error('Failed to create template');
  }

  return response.json();
}

export async function getExportFormats(): Promise<{ formats: Array<{ id: string; name: string; description: string }> }> {
  const response = await fetch(`${API_URL}/api/v1/exports/formats`);

  if (!response.ok) {
    throw new Error('Failed to fetch formats');
  }

  return response.json();
}

export async function batchExport(exports: ExportRequest[]): Promise<{ batch_id: string; results: ExportJob[] }> {
  const response = await fetch(`${API_URL}/api/v1/exports/batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(exports),
  });

  if (!response.ok) {
    throw new Error('Batch export failed');
  }

  return response.json();
}

export async function getExportHistory(limit = 50): Promise<{ exports: ExportJob[]; total: number }> {
  const response = await fetch(`${API_URL}/api/v1/exports/history?limit=${limit}`);

  if (!response.ok) {
    throw new Error('Failed to fetch history');
  }

  return response.json();
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
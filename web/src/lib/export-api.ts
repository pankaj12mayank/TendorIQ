import { unwrapData } from './api-envelope';
import type { ExportFormat, ExportJob } from './export';

const ENTITY_API_SEGMENT: Record<string, string> = {
  proposal: 'proposal',
  checklist: 'checklist',
  risk_analysis: 'risk-analysis',
  tender_document: 'report',
  report: 'report',
};

export function entityExportPath(entityType: string, entityId: string): string {
  const segment = ENTITY_API_SEGMENT[entityType] ?? entityType.replace(/_/g, '-');
  if (segment === 'report') {
    return `/api/v1/exports/export/report/${entityId}`;
  }
  return `/api/v1/exports/export/${segment}/${entityId}`;
}

export function parseExportJob(payload: unknown): ExportJob {
  const raw = (unwrapData(payload) ?? payload) as Record<string, unknown>;
  const format = String(raw.format ?? 'pdf').toLowerCase() as ExportFormat;
  return {
    job_id: String(raw.job_id ?? raw.export_id ?? ''),
    export_id: String(raw.export_id ?? ''),
    status: (raw.status as ExportJob['status']) ?? 'completed',
    format,
    download_url: raw.download_url as string | undefined,
    file_size_bytes: raw.file_size_bytes as number | undefined,
    created_at: String(raw.created_at ?? new Date().toISOString()),
  };
}

export interface ExportHistoryRow {
  export_id: string;
  action?: string;
  user_id?: string;
  timestamp: string;
  details?: Record<string, unknown>;
}

export function mapHistoryRow(row: ExportHistoryRow): ExportJob {
  const details = row.details ?? {};
  const format = String(details.format ?? 'pdf').toLowerCase() as ExportFormat;
  const statusRaw = String(details.status ?? 'completed');
  const status = (
    ['pending', 'processing', 'completed', 'failed'].includes(statusRaw)
      ? statusRaw
      : 'completed'
  ) as ExportJob['status'];

  return {
    job_id: String(details.job_id ?? row.export_id),
    export_id: row.export_id,
    status,
    format,
    file_size_bytes: details.file_size_bytes as number | undefined,
    created_at: row.timestamp,
  };
}

export function parseExportHistory(payload: unknown): { exports: ExportJob[]; total: number } {
  const body = (payload ?? {}) as { exports?: ExportHistoryRow[]; total?: number };
  const rows = body.exports ?? [];
  return {
    exports: rows.map(mapHistoryRow),
    total: body.total ?? rows.length,
  };
}

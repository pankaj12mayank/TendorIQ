import { authenticatedFetch } from './api-fetch';
import { api } from './api-client';
import { parseApiErrorMessage, unwrapData } from './api-envelope';

/** TenderIQ Lite — PDF-only exports (Phase 6). */
export const LITE_EXPORT_FORMAT = 'pdf' as const;
export type LiteExportFormat = typeof LITE_EXPORT_FORMAT;

export interface ExportConfig {
  pdf_only: boolean;
  formats: Array<{
    id: string;
    name: string;
    description: string;
    extension?: string;
    mime_type?: string;
  }>;
}

export async function fetchExportConfig(): Promise<ExportConfig> {
  const raw = await api.get<{ data?: ExportConfig } | ExportConfig>('/api/v1/exports/config');
  return unwrapData(raw as { data?: ExportConfig }) as ExportConfig;
}

export async function downloadTenderAnalysisPdf(tenderId: string): Promise<void> {
  const res = await authenticatedFetch(`/api/v1/exports/tender/${tenderId}/pdf`);
  if (!res.ok) {
    const err = (await res.json().catch(() => ({}))) as Record<string, unknown>;
    const msg = parseApiErrorMessage(err) || 'PDF export failed. Run analysis first.';
    throw new Error(msg);
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `tender-analysis-${tenderId.slice(0, 8)}.pdf`;
  a.click();
  URL.revokeObjectURL(url);
}

export function analysisPdfFilename(tenderId: string): string {
  const date = new Date().toISOString().split('T')[0];
  return `tender-analysis-${date}-${tenderId.slice(0, 8)}.pdf`;
}

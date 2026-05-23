import { describe, expect, it } from 'vitest';

import { entityExportPath, mapHistoryRow, parseExportJob } from '../export-api';

describe('export-api', () => {
  it('maps risk_analysis to hyphenated API path', () => {
    expect(entityExportPath('risk_analysis', 'abc')).toBe(
      '/api/v1/exports/export/risk-analysis/abc'
    );
  });

  it('maps report exports to tender report endpoint', () => {
    expect(entityExportPath('report', 't-1')).toBe('/api/v1/exports/export/report/t-1');
  });

  it('unwraps success/data export job payloads', () => {
    const job = parseExportJob({
      success: true,
      data: {
        export_id: 'e1',
        job_id: 'j1',
        status: 'completed',
        format: 'pdf',
        created_at: '2026-01-01T00:00:00Z',
      },
    });
    expect(job.export_id).toBe('e1');
    expect(job.format).toBe('pdf');
  });

  it('maps export history rows to ExportJob', () => {
    const job = mapHistoryRow({
      export_id: 'e2',
      timestamp: '2026-01-02T00:00:00Z',
      details: { format: 'csv', status: 'completed', job_id: 'j2' },
    });
    expect(job.format).toBe('csv');
    expect(job.job_id).toBe('j2');
  });
});

import { describe, expect, it } from 'vitest';
import {
  mapTenderFromApi,
  parseApiErrorCode,
  parseApiErrorMessage,
  parsePaginated,
  unwrapData,
} from '../api-envelope';

describe('api-envelope', () => {
  it('unwraps success envelopes', () => {
    expect(unwrapData({ success: true, data: { id: '1' } })).toEqual({ id: '1' });
  });

  it('maps snake_case tender fields', () => {
    const t = mapTenderFromApi({
      id: '1',
      title: 'A',
      status: 'draft',
      closing_date: '2026-06-01T00:00:00Z',
      tenant_id: 'org-1',
      created_at: '2026-05-01T00:00:00Z',
      updated_at: '2026-05-02T00:00:00Z',
    });
    expect(t.closingDate).toMatch(/^2026-06-01T00:00:00/);
    expect(t.tenantId).toBe('org-1');
    expect(t.organizationId).toBe('org-1');
  });

  it('parses paginated meta total_pages', () => {
    const page = parsePaginated({
      success: true,
      data: [{ id: '1', title: 'A', status: 'draft' }],
      meta: { page: 1, limit: 20, total: 1, total_pages: 1 },
    });
    expect(page.data).toHaveLength(1);
    expect(page.meta.totalPages).toBe(1);
  });

  it('lifts legacy root pagination fields into meta', () => {
    const page = parsePaginated({
      success: true,
      data: [{ id: 'n1' }],
      total: 42,
      page: 2,
      limit: 10,
    });
    expect(page.meta.total).toBe(42);
    expect(page.meta.page).toBe(2);
    expect(page.meta.limit).toBe(10);
  });

  it('parses nested validation error envelope', () => {
    const msg = parseApiErrorMessage({
      success: false,
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Request validation failed',
        details: [{ loc: ['body', 'email'], msg: 'field required' }],
      },
    });
    expect(msg).toBe('Request validation failed');
    expect(parseApiErrorCode({ error: { code: 'VALIDATION_ERROR' } })).toBe('VALIDATION_ERROR');
  });

  it('parses FastAPI detail array', () => {
    const msg = parseApiErrorMessage({
      detail: [{ loc: ['query', 'page'], msg: 'value is not a valid integer' }],
    });
    expect(msg).toContain('page');
  });
});

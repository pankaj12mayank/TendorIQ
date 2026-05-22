import { describe, expect, it } from 'vitest';
import { mapTenderFromApi, parsePaginated, unwrapData } from '../api-envelope';

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
    expect(t.closingDate).toBe('2026-06-01T00:00:00Z');
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
});

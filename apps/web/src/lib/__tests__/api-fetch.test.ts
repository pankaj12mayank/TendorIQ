import { describe, expect, it } from 'vitest';

import { apiUrl, getApiBaseUrl } from '../api-config';

describe('api-config', () => {
  it('builds absolute paths from relative API routes', () => {
    const base = getApiBaseUrl();
    expect(apiUrl('/api/v1/tenders')).toBe(`${base}/api/v1/tenders`);
    expect(apiUrl('/tenders')).toBe(`${base}/api/v1/tenders`);
  });

  it('passes through absolute URLs', () => {
    expect(apiUrl('https://cdn.example.com/file.pdf')).toBe('https://cdn.example.com/file.pdf');
  });
});

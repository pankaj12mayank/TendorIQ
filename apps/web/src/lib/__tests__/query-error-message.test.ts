import { describe, expect, it } from 'vitest';

import { getQueryErrorMessage } from '../query-error-message';

describe('getQueryErrorMessage', () => {
  it('formats Error instances', () => {
    expect(getQueryErrorMessage(new Error('network down'))).toBe('network down');
  });

  it('returns generic message for unknown errors', () => {
    expect(getQueryErrorMessage({ code: 1 })).toBe('Request failed');
  });

  it('returns null when no error', () => {
    expect(getQueryErrorMessage(null)).toBeNull();
  });
});

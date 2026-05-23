import { describe, expect, it } from 'vitest';

import { formatPollingError, PollingTimeoutError } from '../polling-errors';

describe('polling-errors', () => {
  it('formats timeout with actionable message', () => {
    const err = new PollingTimeoutError('Document processing', 30, 3000);
    expect(formatPollingError(err, 'Document processing')).toMatch(/90s/);
    expect(formatPollingError(err, 'Document processing')).toMatch(/Refresh/i);
  });
});

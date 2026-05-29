import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  notifyUnauthorized,
  resetUnauthorizedNotifyStateForTests,
  setSessionInvalidateHandler,
  setUnauthorizedHandler,
} from '../auth-unauthorized';

describe('auth-unauthorized', () => {
  afterEach(() => {
    setUnauthorizedHandler(null);
    setSessionInvalidateHandler(null);
    resetUnauthorizedNotifyStateForTests();
  });

  it('no-ops in non-browser environments', () => {
    const handler = vi.fn();
    setUnauthorizedHandler(handler);
    notifyUnauthorized();
    expect(handler).not.toHaveBeenCalled();
  });

  it('invokes registered handler when window exists', () => {
    const handler = vi.fn();
    setUnauthorizedHandler(handler);

    vi.stubGlobal('window', {
      location: { pathname: '/dashboard/billing', search: '' },
    });

    notifyUnauthorized();
    expect(handler).toHaveBeenCalledWith({
      pathname: '/dashboard/billing',
      search: '',
    });

    vi.unstubAllGlobals();
  });

  it('redirects dashboard paths to sign-in when no handler', () => {
    let href = '/dashboard/tenders';
    vi.stubGlobal('window', {
      location: {
        pathname: '/dashboard/tenders',
        search: '?tab=open',
        get href() {
          return href;
        },
        set href(value: string) {
          href = value;
        },
      },
    });

    notifyUnauthorized();
    expect(href).toContain('/sign-in');
    expect(href).toContain('redirect_url=');

    vi.unstubAllGlobals();
  });
});

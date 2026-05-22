import { describe, expect, it, vi } from 'vitest';

import { isClerkPublishableKeyConfigured } from '../clerk-env';

describe('isClerkPublishableKeyConfigured', () => {
  it('returns false for placeholder keys', () => {
    vi.stubEnv('NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY', 'pk_test_your_key_here');
    expect(isClerkPublishableKeyConfigured()).toBe(false);
    vi.unstubAllEnvs();
  });

  it('returns true for plausible Clerk publishable keys', () => {
    vi.stubEnv(
      'NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY',
      'pk_test_' + 'a'.repeat(30)
    );
    expect(isClerkPublishableKeyConfigured()).toBe(true);
    vi.unstubAllEnvs();
  });
});

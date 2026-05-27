/** Auth provider — local by default; optional Clerk. */

import { isClerkConfigured } from '@/lib/clerk-config';

export function getAuthProvider(): 'clerk' | 'local' {
  const requested = (
    process.env.NEXT_PUBLIC_AUTH_PROVIDER ||
    process.env.AUTH_PROVIDER ||
    'local'
  ).toLowerCase();
  if (requested === 'clerk' && isClerkConfigured()) return 'clerk';
  return 'local';
}

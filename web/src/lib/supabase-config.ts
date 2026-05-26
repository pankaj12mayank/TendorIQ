/** Auth provider — defaults to local email/password when cloud keys are missing. */

import { isClerkConfigured } from '@/lib/clerk-config';

export function getAuthProvider(): 'clerk' | 'supabase' | 'local' {
  const requested = (
    process.env.NEXT_PUBLIC_AUTH_PROVIDER ||
    process.env.AUTH_PROVIDER ||
    'local'
  ).toLowerCase();
  if (requested === 'supabase' && isSupabaseConfigured()) return 'supabase';
  if (requested === 'clerk' && isClerkConfigured()) return 'clerk';
  return 'local';
}

export function isSupabaseConfigured(): boolean {
  const url = (process.env.NEXT_PUBLIC_SUPABASE_URL || '').trim();
  const key = (process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '').trim();
  return (
    url.length > 10 &&
    !url.includes('placeholder') &&
    key.length > 10 &&
    !key.includes('placeholder')
  );
}

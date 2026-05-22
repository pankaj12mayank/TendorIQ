import { getStoredSession } from '@/lib/auth-session';
import { buildApiAuthHeaders } from '@/lib/auth-user';

/** Auth + tenant headers from the active browser session. */
export function getSessionRequestHeaders(): HeadersInit {
  const session = getStoredSession();
  if (!session) return {};
  return buildApiAuthHeaders(session.token, session.user);
}

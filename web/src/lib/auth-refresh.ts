import { refreshAccessToken } from '@/lib/auth-api';
import { getRefreshToken, readPersistedAuthUser, setStoredSession } from '@/lib/auth-session';

let refreshInFlight: Promise<boolean> | null = null;

/** Refresh access token once (shared across concurrent 401s). */
export async function attemptSessionRefresh(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const payload = await refreshAccessToken(refreshToken);
        if (!payload?.access_token) return false;

        const user = readPersistedAuthUser();
        if (!user) return false;

        setStoredSession(payload.access_token, user, {
          refreshToken: payload.refresh_token ?? refreshToken,
          expiresInSec: payload.expires_in,
        });
        return true;
      } catch {
        return false;
      } finally {
        refreshInFlight = null;
      }
    })();
  }

  return refreshInFlight;
}

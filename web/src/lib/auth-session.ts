import type { SessionUser } from '@/shared/auth';

/** @deprecated Use SessionUser from @/shared/auth */
export type AuthUser = SessionUser;

const TOKEN_KEY = 'tenderiq_auth_token';
const REFRESH_KEY = 'tenderiq_auth_refresh';
const USER_KEY = 'tenderiq_auth_user';
const EXPIRES_KEY = 'tenderiq_auth_expires_at';
const LAST_ACTIVE_KEY = 'tenderiq_auth_last_active';

/** One-day session lifecycle (Layer 1 security baseline). */
export const SESSION_MAX_AGE_MS = 24 * 60 * 60 * 1000;

export interface StoredAuthSession {
  token: string;
  refreshToken?: string;
  user: AuthUser;
  expiresAt: number;
}

export function isSessionExpired(expiresAt: number): boolean {
  return Date.now() >= expiresAt;
}

/** Single source for the bearer token (localStorage; mirrored to `__session` cookie). */
export function getAuthToken(): string | null {
  return getStoredSession()?.token ?? null;
}

export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(REFRESH_KEY);
}

/** Read cached user without clearing session when access token metadata is stale. */
export function readPersistedAuthUser(): AuthUser | null {
  if (typeof window === 'undefined') return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function getStoredSession(): StoredAuthSession | null {
  if (typeof window === 'undefined') return null;
  const token = localStorage.getItem(TOKEN_KEY);
  const raw = localStorage.getItem(USER_KEY);
  const expiresRaw = localStorage.getItem(EXPIRES_KEY);
  if (!token || !raw) return null;

  const expiresAt = expiresRaw ? Number(expiresRaw) : 0;
  if (!expiresAt || isSessionExpired(expiresAt)) {
    clearStoredSession();
    return null;
  }

  try {
    const refreshToken = localStorage.getItem(REFRESH_KEY) ?? undefined;
    return { token, refreshToken, user: JSON.parse(raw) as AuthUser, expiresAt };
  } catch {
    clearStoredSession();
    return null;
  }
}

export function setStoredSession(
  token: string,
  user: AuthUser,
  options?: { refreshToken?: string; expiresInSec?: number }
): void {
  const sessionMaxSec = Math.floor(SESSION_MAX_AGE_MS / 1000);
  const requested = options?.expiresInSec;
  const maxAgeSec =
    requested && requested >= 60 ? Math.min(requested, sessionMaxSec) : sessionMaxSec;
  const expiresAt = Date.now() + maxAgeSec * 1000;
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  localStorage.setItem(EXPIRES_KEY, String(expiresAt));
  if (options?.refreshToken) {
    localStorage.setItem(REFRESH_KEY, options.refreshToken);
  }
  localStorage.setItem(LAST_ACTIVE_KEY, String(Date.now()));
  const secure = window.location.protocol === 'https:' ? '; Secure' : '';
  document.cookie = `__session=${token}; path=/; max-age=${maxAgeSec}; SameSite=Strict${secure}`;
}

export function clearStoredSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(EXPIRES_KEY);
  localStorage.removeItem(LAST_ACTIVE_KEY);
  document.cookie = '__session=; path=/; max-age=0';
}

export function getSessionTimeRemainingMs(): number {
  const session = getStoredSession();
  if (!session) return 0;
  return Math.max(0, session.expiresAt - Date.now());
}

export function markSessionActivity(): void {
  if (typeof window === 'undefined') return;
  if (!localStorage.getItem(TOKEN_KEY)) return;
  localStorage.setItem(LAST_ACTIVE_KEY, String(Date.now()));
}

export function getSessionLastActivityMs(): number {
  if (typeof window === 'undefined') return 0;
  return Number(localStorage.getItem(LAST_ACTIVE_KEY) || 0);
}

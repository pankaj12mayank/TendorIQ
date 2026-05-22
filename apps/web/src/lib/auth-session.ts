export interface AuthUser {
  id: string;
  email: string;
  name: string;
  imageUrl?: string;
  /** Platform (`super_admin`) or display role from API. */
  role?: string;
  /** Tenant membership role for RBAC (`owner`, `admin`, `manager`, …). */
  membershipRole?: string;
  tenantId?: string;
  permissions?: string[];
}

const TOKEN_KEY = 'tenderiq_auth_token';
const REFRESH_KEY = 'tenderiq_auth_refresh';
const USER_KEY = 'tenderiq_auth_user';
const EXPIRES_KEY = 'tenderiq_auth_expires_at';

/** Default session lifetime when API omits expires_in (30 min JWT default). */
export const SESSION_MAX_AGE_MS = 30 * 60 * 1000;

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
  const maxAgeSec = options?.expiresInSec ?? Math.floor(SESSION_MAX_AGE_MS / 1000);
  const expiresAt = Date.now() + maxAgeSec * 1000;
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  localStorage.setItem(EXPIRES_KEY, String(expiresAt));
  if (options?.refreshToken) {
    localStorage.setItem(REFRESH_KEY, options.refreshToken);
  }
  document.cookie = `__session=${token}; path=/; max-age=${maxAgeSec}; SameSite=Lax`;
}

export function clearStoredSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(EXPIRES_KEY);
  document.cookie = '__session=; path=/; max-age=0';
}

export function getSessionTimeRemainingMs(): number {
  const session = getStoredSession();
  if (!session) return 0;
  return Math.max(0, session.expiresAt - Date.now());
}

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  imageUrl?: string;
  role?: string;
  permissions?: string[];
}

const TOKEN_KEY = 'tenderiq_auth_token';
const USER_KEY = 'tenderiq_auth_user';
const EXPIRES_KEY = 'tenderiq_auth_expires_at';

/** Session lifetime: 24 hours */
export const SESSION_MAX_AGE_MS = 24 * 60 * 60 * 1000;

export interface StoredAuthSession {
  token: string;
  user: AuthUser;
  expiresAt: number;
}

export function isSessionExpired(expiresAt: number): boolean {
  return Date.now() >= expiresAt;
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
    return { token, user: JSON.parse(raw) as AuthUser, expiresAt };
  } catch {
    clearStoredSession();
    return null;
  }
}

export function setStoredSession(token: string, user: AuthUser): void {
  const expiresAt = Date.now() + SESSION_MAX_AGE_MS;
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  localStorage.setItem(EXPIRES_KEY, String(expiresAt));
  const maxAgeSec = Math.floor(SESSION_MAX_AGE_MS / 1000);
  document.cookie = `__session=${token}; path=/; max-age=${maxAgeSec}; SameSite=Lax`;
}

export function clearStoredSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(EXPIRES_KEY);
  document.cookie = '__session=; path=/; max-age=0';
}

export function getSessionTimeRemainingMs(): number {
  const session = getStoredSession();
  if (!session) return 0;
  return Math.max(0, session.expiresAt - Date.now());
}

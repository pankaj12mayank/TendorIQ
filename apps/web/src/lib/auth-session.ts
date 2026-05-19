export interface AuthUser {
  id: string;
  email: string;
  name: string;
  imageUrl?: string;
  role?: string;
}

const TOKEN_KEY = 'tenderiq_auth_token';
const USER_KEY = 'tenderiq_auth_user';

export interface StoredAuthSession {
  token: string;
  user: AuthUser;
}

export function getStoredSession(): StoredAuthSession | null {
  if (typeof window === 'undefined') return null;
  const token = localStorage.getItem(TOKEN_KEY);
  const raw = localStorage.getItem(USER_KEY);
  if (!token || !raw) return null;
  try {
    return { token, user: JSON.parse(raw) as AuthUser };
  } catch {
    return null;
  }
}

export function setStoredSession(token: string, user: AuthUser): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  document.cookie = `__session=${token}; path=/; max-age=${60 * 60 * 24 * 7}; SameSite=Lax`;
}

export function clearStoredSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  document.cookie = '__session=; path=/; max-age=0';
}

'use client';

import dynamic from 'next/dynamic';
import { useRouter, usePathname } from 'next/navigation';
import {
  useEffect,
  useCallback,
  useContext,
  useState,
  useMemo,
  type ReactNode,
} from 'react';

import {
  clearStoredSession,
  getStoredSession,
  setStoredSession,
  type AuthUser,
} from '@/lib/auth-session';
import { isClerkConfigured, isProtectedPath } from '@/lib/clerk-config';

import { AuthContext, type AuthContextValue } from './auth-context';

export type { AuthUser, AuthContextValue };

const ClerkAuthProvider = dynamic(
  () => import('./clerk-auth-provider').then((m) => m.ClerkAuthProvider),
  { ssr: false }
);

function useRouteGuard(isAuthenticated: boolean, isLoading: boolean, role?: string) {
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (isLoading) return;

    if (!isAuthenticated && isProtectedPath(pathname)) {
      const target = pathname.includes('/admin') ? '/admin/login' : '/sign-in';
      const url = new URL(target, window.location.origin);
      if (target === '/sign-in') {
        url.searchParams.set('redirect_url', pathname);
      }
      router.replace(url.toString());
      return;
    }

    if (isAuthenticated && (pathname === '/sign-in' || pathname === '/sign-up')) {
      router.replace(role === 'super_admin' ? '/dashboard/admin' : '/onboarding');
    }
  }, [isAuthenticated, isLoading, pathname, router, role]);
}

function LocalAuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const session = getStoredSession();
    setUser(session?.user ?? null);
    setIsLoading(false);
  }, []);

  useRouteGuard(!!user, isLoading, user?.role);

  const signOut = useCallback(async () => {
    clearStoredSession();
    setUser(null);
    router.push('/');
  }, [router]);

  const getToken = useCallback(async () => getStoredSession()?.token ?? null, []);

  const loginWithSuperAdmin = useCallback(
    async (email: string, password: string) => {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error((err as { detail?: string }).detail || 'Login failed');
      }
      const data = await res.json();
      const authUser: AuthUser = {
        id: data.user?.email ?? email,
        email: data.user?.email ?? email,
        name: data.user?.name ?? 'Super Admin',
        role: 'super_admin',
      };
      setStoredSession(data.token, authUser);
      setUser(authUser);
      router.push('/dashboard/admin');
    },
    [router]
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated: !!user,
      isLoading,
      user,
      signOut,
      getToken,
      loginWithSuperAdmin,
    }),
    [user, isLoading, signOut, getToken, loginWithSuperAdmin]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  if (isClerkConfigured()) {
    return <ClerkAuthProvider>{children}</ClerkAuthProvider>;
  }
  return <LocalAuthProvider>{children}</LocalAuthProvider>;
}

export function useAuthContext() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext must be used within AuthProvider');
  }
  return context;
}

export function useAuth() {
  const { isAuthenticated, isLoading, user } = useAuthContext();
  return {
    isLoaded: !isLoading,
    isSignedIn: isAuthenticated,
    userId: user?.id ?? null,
  };
}

export function useAuthState() {
  const { isAuthenticated, isLoading, user } = useAuthContext();
  return { isAuthenticated, isLoading, user };
}

export function useCurrentUser() {
  const { user } = useAuthContext();
  return user;
}

export function useSignOut() {
  const { signOut } = useAuthContext();
  return signOut;
}

export function useGetToken() {
  const { getToken } = useAuthContext();
  return getToken;
}

export function useSuperAdminLogin() {
  const { loginWithSuperAdmin } = useAuthContext();
  return loginWithSuperAdmin;
}

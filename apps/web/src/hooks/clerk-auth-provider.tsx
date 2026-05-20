'use client';

import { useAuth as useClerkAuth, useUser, useSession } from '@clerk/nextjs';
import { useRouter, usePathname } from 'next/navigation';
import { useEffect, useCallback, useMemo, type ReactNode } from 'react';

import {
  clearStoredSession,
  getStoredSession,
  setStoredSession,
  type AuthUser,
} from '@/lib/auth-session';
import { getPostLoginPath } from '@/lib/auth-redirect';
import { isProtectedPath } from '@/lib/clerk-config';
import { getRolePermissions } from '@/lib/permissions';
import { toast } from 'sonner';

import { AuthContext, type AuthContextValue } from './auth-context';

function useRouteGuard(isAuthenticated: boolean, isLoading: boolean, role?: string) {
  const router = useRouter();
  const pathname = usePathname();
  useEffect(() => {
    if (isLoading) return;

    if (!isAuthenticated && isProtectedPath(pathname)) {
      const url = new URL('/sign-in', window.location.origin);
      const redirect = pathname + window.location.search;
      url.searchParams.set('redirect_url', redirect);
      router.replace(url.toString());
      return;
    }

    if (isAuthenticated && (pathname === '/sign-in' || pathname === '/sign-up')) {
      const params = new URLSearchParams(window.location.search);
      const redirectUrl = params.get('redirect_url');
      if (redirectUrl && redirectUrl.startsWith('/dashboard')) {
        router.replace(redirectUrl);
      } else {
        router.replace(getPostLoginPath(role));
      }
    }
  }, [isAuthenticated, isLoading, pathname, router, role]);
}

export function ClerkAuthProvider({ children }: { children: ReactNode }) {
  const { isLoaded, isSignedIn, signOut: clerkSignOut } = useClerkAuth();
  const { user } = useUser();
  const { getToken: clerkGetToken } = useSession();
  const router = useRouter();
  const pathname = usePathname();

  const stored = typeof window !== 'undefined' ? getStoredSession() : null;

  const authUser: AuthUser | null = user
    ? {
        id: user.id,
        email: user.emailAddresses[0]?.emailAddress || '',
        name: user.fullName || user.username || '',
        imageUrl: user.imageUrl,
        role: (user.publicMetadata?.role as string | undefined) ?? stored?.user.role,
        permissions: getRolePermissions(
          (user.publicMetadata?.role as string | undefined) ?? stored?.user.role
        ),
      }
    : stored?.user ?? null;

  const isAuthenticated = (isLoaded && !!isSignedIn) || !!stored;

  useRouteGuard(isAuthenticated, !isLoaded, authUser?.role);

  useEffect(() => {
    if (!isLoaded || !isSignedIn || !authUser) return;
    if (authUser.role === 'super_admin' && pathname.startsWith('/dashboard') && !pathname.includes('/admin')) {
      router.replace('/dashboard/admin');
    }
  }, [isLoaded, isSignedIn, authUser, pathname, router]);

  const signOut = useCallback(async () => {
    clearStoredSession();
    await clerkSignOut();
    router.push('/');
  }, [clerkSignOut, router]);

  const getToken = useCallback(async () => {
    try {
      return (await clerkGetToken()) ?? getStoredSession()?.token ?? null;
    } catch {
      return getStoredSession()?.token ?? null;
    }
  }, [clerkGetToken]);

  const loginWithCredentials = useCallback(
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
      const role = (data.user?.role as string) || 'user';
      const sessionUser: AuthUser = {
        id: data.user?.email ?? email,
        email: data.user?.email ?? email,
        name: data.user?.name ?? email.split('@')[0] ?? 'User',
        role,
        permissions: getRolePermissions(role),
      };
      setStoredSession(data.token, sessionUser);
      toast.success('Signed in successfully');
      router.push(getPostLoginPath(role));
    },
    [router]
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated,
      isLoading: !isLoaded,
      user: authUser,
      signOut,
      getToken,
      loginWithCredentials,
    }),
    [isAuthenticated, isLoaded, authUser, signOut, getToken, loginWithCredentials]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

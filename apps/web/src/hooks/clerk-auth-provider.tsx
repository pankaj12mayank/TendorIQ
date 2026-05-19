'use client';

import { useAuth as useClerkAuth, useUser, useSession } from '@clerk/nextjs';
import { useRouter, usePathname } from 'next/navigation';
import { useEffect, useCallback, useMemo, type ReactNode } from 'react';

import {
  clearStoredSession,
  getStoredSession,
  type AuthUser,
} from '@/lib/auth-session';
import { isProtectedPath } from '@/lib/clerk-config';

import { AuthContext, type AuthContextValue } from './auth-context';

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

export function ClerkAuthProvider({ children }: { children: ReactNode }) {
  const { isLoaded, isSignedIn, signOut: clerkSignOut } = useClerkAuth();
  const { user } = useUser();
  const { getToken: clerkGetToken } = useSession();
  const router = useRouter();
  const pathname = usePathname();

  const authUser: AuthUser | null = user
    ? {
        id: user.id,
        email: user.emailAddresses[0]?.emailAddress || '',
        name: user.fullName || user.username || '',
        imageUrl: user.imageUrl,
        role: user.publicMetadata?.role as string | undefined,
      }
    : null;

  useRouteGuard(isLoaded && !!isSignedIn, !isLoaded, authUser?.role);

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

  const loginWithSuperAdmin = useCallback(async () => {
    throw new Error('Use /admin/login for super admin credentials');
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated: isLoaded && !!isSignedIn,
      isLoading: !isLoaded,
      user: authUser,
      signOut,
      getToken,
      loginWithSuperAdmin,
    }),
    [isLoaded, isSignedIn, authUser, signOut, getToken, loginWithSuperAdmin]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

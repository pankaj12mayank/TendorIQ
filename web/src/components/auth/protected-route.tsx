'use client';

import { useAuthState } from '@/hooks/use-auth';
import { getMembershipRole } from '@/lib/auth-user';
import { hasPermission } from '@/lib/permissions';
import { LoadingState } from '@/components/ui/loading-state';
import { ROUTES } from '@/lib/routes';
import { getPostLoginPath } from '@/lib/auth-redirect';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect } from 'react';

interface ProtectedRouteProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  requiredRoles?: ('super_admin' | 'owner' | 'admin' | 'manager' | 'analyst' | 'member' | 'viewer')[];
  requiredPermission?: string;
}

export function ProtectedRoute({
  children,
  fallback,
  requiredRoles,
  requiredPermission,
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuthState();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (isLoading || isAuthenticated) return;
    const url = new URL(ROUTES.signIn, window.location.origin);
    url.searchParams.set('redirect_url', pathname);
    router.replace(url.pathname + url.search);
  }, [isLoading, isAuthenticated, pathname, router]);

  if (isLoading) {
    return <LoadingState message="Checking authentication..." />;
  }

  if (!isAuthenticated) {
    if (fallback) return <>{fallback}</>;
    return <LoadingState message="Redirecting to sign in..." />;
  }

  if (requiredRoles && requiredRoles.length > 0) {
    const userRole = getMembershipRole(user);

    if (!requiredRoles.includes(userRole as (typeof requiredRoles)[number])) {
      if (fallback) return <>{fallback}</>;

      return (
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-center">
            <h2 className="text-lg font-semibold">Access Denied</h2>
            <p className="text-muted-foreground">
              You don't have permission to access this page.
            </p>
          </div>
        </div>
      );
    }
  }

  if (requiredPermission) {
    const allowed = hasPermission(
      getMembershipRole(user),
      requiredPermission,
      user?.permissions
    );
    if (!allowed) {
      if (fallback) return <>{fallback}</>;
      return (
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-center">
            <h2 className="text-lg font-semibold">Access Denied</h2>
            <p className="text-muted-foreground">
              You don't have permission to access this page.
            </p>
          </div>
        </div>
      );
    }
  }

  return <>{children}</>;
}


interface GuestRouteProps {
  children: React.ReactNode;
}

function isGuestAuthPath(pathname: string): boolean {
  return (
    pathname === ROUTES.signIn ||
    pathname.startsWith(`${ROUTES.signIn}/`) ||
    pathname === ROUTES.signUp ||
    pathname.startsWith(`${ROUTES.signUp}/`) ||
    pathname === ROUTES.forgotPassword ||
    pathname.startsWith(`${ROUTES.forgotPassword}/`)
  );
}

export function GuestRoute({ children }: GuestRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuthState();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (isLoading || !isAuthenticated) return;
    if (!isGuestAuthPath(pathname)) return;

    const params = new URLSearchParams(window.location.search);
    const redirectUrl = params.get('redirect_url');
    if (redirectUrl && redirectUrl.startsWith('/dashboard')) {
      router.replace(redirectUrl);
      return;
    }
    router.replace(getPostLoginPath(user?.membershipRole ?? user?.role));
  }, [isLoading, isAuthenticated, pathname, router, user]);

  if (isLoading) {
    return <LoadingState message="Loading..." />;
  }

  if (isAuthenticated) {
    return <LoadingState message="Redirecting..." />;
  }

  return <>{children}</>;
}
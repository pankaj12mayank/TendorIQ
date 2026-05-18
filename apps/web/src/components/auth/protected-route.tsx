'use client';

import { useAuthState } from '@/hooks/use-auth';
import { LoadingState } from '@/components/ui/loading-state';
import { usePathname } from 'next/navigation';
import { useEffect } from 'react';

interface ProtectedRouteProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  requiredRoles?: ('super_admin' | 'tenant_admin' | 'user')[];
}

export function ProtectedRoute({
  children,
  fallback,
  requiredRoles,
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuthState();
  const pathname = usePathname();

  if (isLoading) {
    return <LoadingState message="Checking authentication..." />;
  }

  if (!isAuthenticated) {
    if (fallback) return <>{fallback}</>;

    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <h2 className="text-lg font-semibold">Authentication Required</h2>
          <p className="text-muted-foreground">Please sign in to continue.</p>
        </div>
      </div>
    );
  }

  if (requiredRoles && requiredRoles.length > 0) {
    const userRole = user?.role || 'user';

    if (!requiredRoles.includes(userRole as 'super_admin' | 'tenant_admin' | 'user')) {
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

export function GuestRoute({ children }: GuestRouteProps) {
  const { isAuthenticated, isLoading } = useAuthState();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      const redirectUrl = pathname || '/dashboard';
      window.location.href = redirectUrl;
    }
  }, [isLoading, isAuthenticated, pathname]);

  if (isLoading) {
    return <LoadingState message="Loading..." />;
  }

  if (isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
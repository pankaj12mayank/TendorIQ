'use client';

import { useEffect, type ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { AlertCircle } from 'lucide-react';

import { useAuth, useCurrentUser } from '@/hooks/use-auth';
import { canAccessAdminConsole } from '@/lib/permissions';
import { LoadingState } from '@/components/ui/loading-state';

export function AdminRouteGuard({ children }: { children: ReactNode }) {
  const { isLoaded, isSignedIn } = useAuth();
  const user = useCurrentUser();
  const router = useRouter();

  useEffect(() => {
    if (!isLoaded) return;
    if (!isSignedIn) {
      router.replace('/sign-in?redirect_url=/dashboard/admin');
      return;
    }
    if (!canAccessAdminConsole(user?.role)) {
      router.replace('/dashboard');
    }
  }, [isLoaded, isSignedIn, user?.role, router]);

  if (!isLoaded) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <LoadingState message="Loading admin console..." />
      </div>
    );
  }

  if (!isSignedIn || !canAccessAdminConsole(user?.role)) {
    return null;
  }

  return <>{children}</>;
}

export function AccessDenied({ message }: { message?: string }) {
  return (
    <div className="flex min-h-[40vh] items-center justify-center">
      <div className="text-center">
        <AlertCircle className="mx-auto mb-4 h-12 w-12 text-destructive" />
        <h3 className="text-lg font-medium">Access denied</h3>
        <p className="mt-2 text-sm text-muted-foreground">
          {message ?? 'You do not have permission to view this section.'}
        </p>
      </div>
    </div>
  );
}

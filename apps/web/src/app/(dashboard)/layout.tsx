'use client';

import { Suspense, useEffect, useMemo, useState } from 'react';
import { useAuth, useCurrentUser } from '@/hooks/use-auth';
import { useRouter, usePathname } from 'next/navigation';
import { canAccessAdminConsole, canAccessTenantDashboard, isSuperAdmin } from '@/lib/permissions';
import { isSuperAdminTenantViewActive } from '@/lib/super-admin-tenant-view';
import { fetchOnboardingStatusAuthenticated } from '@/lib/onboarding-api';

import { Sidebar } from '@/components/layout/sidebar';
import { Header } from '@/components/layout/header';
import { MobileNav } from '@/components/layout/mobile-nav';
import { DashboardBootLoading, SidebarSkeleton } from '@/components/layout/dashboard-loading';
import { Toaster } from '@/components/ui/sonner';
import { toast } from 'sonner';
import { LoadingState } from '@/components/ui/loading-state';
import { getAuthToken } from '@/lib/auth-session';

const ONBOARDING_CHECK_TIMEOUT_MS = 12_000;

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isLoaded, userId } = useAuth();
  const user = useCurrentUser();
  const router = useRouter();
  const pathname = usePathname();
  const isAdminConsole = pathname.startsWith('/dashboard/admin');
  const [mounted, setMounted] = useState(false);
  const [checkedOnboarding, setCheckedOnboarding] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (isLoaded && !userId) {
      router.push('/sign-in');
    }
  }, [isLoaded, userId, router]);

  useEffect(() => {
    let cancelled = false;

    async function checkOnboarding() {
      if (!isLoaded || !userId) return;

      if (user?.role === 'super_admin') {
        if (!cancelled) setCheckedOnboarding(true);
        return;
      }

      const token = getAuthToken();
      if (!token) {
        if (!cancelled) setCheckedOnboarding(true);
        return;
      }

      try {
        const status = await Promise.race([
          fetchOnboardingStatusAuthenticated(token),
          new Promise<never>((_, reject) => {
            setTimeout(
              () => reject(new Error('Onboarding verification timed out')),
              ONBOARDING_CHECK_TIMEOUT_MS
            );
          }),
        ]);

        if (cancelled) return;

        if (!status.is_completed) {
          router.replace('/onboarding');
          return;
        }

        setCheckedOnboarding(true);
      } catch {
        if (cancelled) return;
        toast.error('Could not verify workspace setup. Please complete onboarding.');
        router.replace('/onboarding');
      }
    }

    void checkOnboarding();

    return () => {
      cancelled = true;
    };
  }, [isLoaded, userId, user?.role, router]);

  useEffect(() => {
    if (isAdminConsole && user && !canAccessAdminConsole(user.role)) {
      router.replace('/dashboard');
      return;
    }
    if (
      !isAdminConsole &&
      user &&
      isSuperAdmin(user.role) &&
      !isSuperAdminTenantViewActive()
    ) {
      router.replace('/dashboard/admin');
    }
  }, [isAdminConsole, user, router]);

  const tenantDashboardAllowed = user
    ? canAccessTenantDashboard(user.role) ||
      (isSuperAdmin(user.role) && isSuperAdminTenantViewActive())
    : true;

  const bootMessage = useMemo(() => {
    if (!isLoaded) return 'Loading your session...';
    if (!checkedOnboarding) return 'Checking workspace setup...';
    return 'Loading dashboard...';
  }, [isLoaded, checkedOnboarding]);

  if (!mounted || !isLoaded || !checkedOnboarding) {
    return <DashboardBootLoading message={bootMessage} />;
  }

  if (!userId) {
    return null;
  }

  if (!isAdminConsole && user && !tenantDashboardAllowed) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingState message="Redirecting to admin console..." />
      </div>
    );
  }

  if (isAdminConsole && user && !canAccessAdminConsole(user.role)) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingState message="Redirecting..." />
      </div>
    );
  }

  if (isAdminConsole) {
    return (
      <>
        <div className="flex min-h-screen flex-col">
          <Header />
          <main className="flex-1 overflow-hidden">{children}</main>
        </div>
        <Toaster />
      </>
    );
  }

  return (
    <>
      <div className="flex min-h-screen">
        <Suspense fallback={<SidebarSkeleton />}>
          <Sidebar />
        </Suspense>
        <div className="flex min-w-0 flex-1 flex-col">
          <MobileNav />
          <Header />
          <main className="flex-1 overflow-y-auto scroll-premium p-6 md:p-8">
            <div className="mx-auto max-w-7xl animate-fade-in">{children}</div>
          </main>
        </div>
      </div>
      <Toaster />
    </>
  );
}

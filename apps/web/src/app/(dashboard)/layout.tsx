'use client';

import { Suspense, useEffect, useMemo, useState } from 'react';
import { useAuth, useCurrentUser } from '@/hooks/use-auth';
import { useRouter, usePathname } from 'next/navigation';
import { canAccessAdminConsole, canAccessTenantDashboard, isSuperAdmin } from '@/lib/permissions';

import { Sidebar } from '@/components/layout/sidebar';
import { Header } from '@/components/layout/header';
import { MobileNav } from '@/components/layout/mobile-nav';
import { DashboardBootLoading, SidebarSkeleton } from '@/components/layout/dashboard-loading';
import { Toaster } from '@/components/ui/sonner';
import { useOnboardingApi } from '@/hooks/use-onboarding';
import { LoadingState } from '@/components/ui/loading-state';

const ONBOARDING_CHECK_TIMEOUT_MS = 8_000;

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
  const { fetchStatus } = useOnboardingApi();

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

    const timeoutId = window.setTimeout(() => {
      if (!cancelled) setCheckedOnboarding(true);
    }, ONBOARDING_CHECK_TIMEOUT_MS);

    async function checkOnboarding() {
      if (!isLoaded || !userId) return;
      if (user?.role === 'super_admin') {
        setCheckedOnboarding(true);
        return;
      }
      try {
        const status = await fetchStatus();
        if (cancelled) return;
        if (!status.is_completed) {
          router.push('/onboarding');
          return;
        }
      } catch {
        // Fail open — user may already have tenant context from JWT
      }
      if (!cancelled) setCheckedOnboarding(true);
    }

    void checkOnboarding();

    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
    };
  }, [isLoaded, userId, user?.role, fetchStatus, router]);

  useEffect(() => {
    if (isAdminConsole && user && !canAccessAdminConsole(user.role)) {
      router.replace('/dashboard');
      return;
    }
    if (!isAdminConsole && user && isSuperAdmin(user.role)) {
      router.replace('/dashboard/admin');
    }
  }, [isAdminConsole, user, router]);

  const tenantDashboardAllowed = user ? canAccessTenantDashboard(user.role) : true;

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

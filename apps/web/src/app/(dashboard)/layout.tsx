'use client';

import { Suspense, useEffect, useState } from 'react';
import { useAuth, useCurrentUser } from '@/hooks/use-auth';
import { useRouter, usePathname } from 'next/navigation';
import { canAccessAdminConsole } from '@/lib/permissions';

import { Sidebar } from '@/components/layout/sidebar';
import { Header } from '@/components/layout/header';
import { MobileNav } from '@/components/layout/mobile-nav';
import { Toaster } from '@/components/ui/sonner';
import { useOnboardingStore } from '@/stores/onboarding-store';
import { useOnboardingApi } from '@/hooks/use-onboarding';
import { LoadingState } from '@/components/ui/loading-state';

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
  const store = useOnboardingStore();
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
    async function checkOnboarding() {
      if (!isLoaded || !userId) return;
      if (user?.role === 'super_admin') {
        setCheckedOnboarding(true);
        return;
      }
      try {
        const status = await fetchStatus();
        if (!status.is_completed) {
          router.push('/onboarding');
          return;
        }
      } catch {
        // If error, allow dashboard access (user might have existing tenant)
      }
      setCheckedOnboarding(true);
    }
    checkOnboarding();
  }, [isLoaded, userId, user?.role, fetchStatus, router]);

  useEffect(() => {
    if (isAdminConsole && user && !canAccessAdminConsole(user.role)) {
      router.replace('/dashboard');
    }
  }, [isAdminConsole, user, router]);

  if (!mounted || !isLoaded || !checkedOnboarding) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingState message="Loading..." />
      </div>
    );
  }

  if (!userId) {
    return null;
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
        <Suspense fallback={<aside className="hidden w-64 lg:block" />}>
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
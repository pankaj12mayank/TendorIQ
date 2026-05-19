'use client';

import { useAuth, useCurrentUser } from '@/hooks/use-auth';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

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

  return (
    <>
      <div className="flex min-h-screen">
        <Sidebar />
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
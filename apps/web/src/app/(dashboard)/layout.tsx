'use client';

import { useAuth, SignedIn } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import { Sidebar } from '@/components/layout/sidebar';
import { Header } from '@/components/layout/header';
import { MobileNav } from '@/components/layout/mobile-nav';
import { Toaster } from '@/components/ui/toaster';
import { useOnboardingStore } from '@/stores/onboarding-store';
import { useOnboardingApi } from '@/hooks/use-onboarding';
import { LoadingState } from '@/components/ui/loading-state';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isLoaded, userId } = useAuth();
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
  }, [isLoaded, userId, fetchStatus, router]);

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
    <SignedIn>
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="flex flex-1 flex-col">
          <MobileNav />
          <Header />
          <main className="flex-1 overflow-y-auto bg-background p-6">
            {children}
          </main>
        </div>
      </div>
      <Toaster />
    </SignedIn>
  );
}
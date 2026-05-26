'use client';

import { Suspense, useEffect, useState } from 'react';
import { useAuth } from '@/hooks/use-auth';
import { useRouter } from 'next/navigation';
import { Sidebar } from '@/components/layout/sidebar';
import { Header } from '@/components/layout/header';
import { MobileNav } from '@/components/layout/mobile-nav';
import { PageContent } from '@/components/layout/page-content';
import { DashboardBootLoading, SidebarSkeleton } from '@/components/layout/dashboard-loading';
import { Toaster } from '@/components/ui/sonner';
import { ROUTES } from '@/lib/routes';
import { SubscriptionExpiredBanner } from '@/components/billing/subscription-gate';
import { CinematicBackground } from '@/components/cinematic/cinematic-background';
import { usePathname, useSearchParams } from 'next/navigation';

function ExpiredPlanBanner() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const isBillingTab =
    pathname === ROUTES.settings && searchParams.get('tab') === 'billing';
  if (isBillingTab) return null;
  return <SubscriptionExpiredBanner />;
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isLoaded, userId } = useAuth();
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (isLoaded && !userId) {
      router.push(ROUTES.signIn);
    }
  }, [isLoaded, userId, router]);

  if (!mounted || !isLoaded) {
    return <DashboardBootLoading message="Loading workspace..." />;
  }

  if (!userId) {
    return <DashboardBootLoading message="Signing in..." />;
  }

  return (
    <div className="dashboard-shell flex min-h-screen">
      <CinematicBackground intensity="subtle" interactive={false} className="fixed inset-0 z-0" />
      <Suspense fallback={<SidebarSkeleton />}>
        <Sidebar />
      </Suspense>
      <MobileNav />
      <div className="relative z-10 flex min-h-screen flex-1 flex-col lg:pl-[var(--sidebar-width)]">
        <Header />
        <main className="flex-1">
          <PageContent>
            <Suspense fallback={null}>
              <ExpiredPlanBanner />
            </Suspense>
            {children}
          </PageContent>
        </main>
      </div>
      <Toaster richColors closeButton position="top-right" />
    </div>
  );
}

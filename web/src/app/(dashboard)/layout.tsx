'use client';

import { Suspense, useEffect, useState } from 'react';
import { useAuth, useCurrentUser } from '@/hooks/use-auth';
import { useRouter, usePathname } from 'next/navigation';
import { isSuperAdmin } from '@/lib/permissions';
import { Sidebar } from '@/components/layout/sidebar';
import { Header } from '@/components/layout/header';
import { MobileNav } from '@/components/layout/mobile-nav';
import { DashboardBootLoading, SidebarSkeleton } from '@/components/layout/dashboard-loading';
import { Toaster } from '@/components/ui/sonner';
import { ROUTES } from '@/lib/routes';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isLoaded, userId } = useAuth();
  const user = useCurrentUser();
  const router = useRouter();
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (isLoaded && !userId) {
      router.push(ROUTES.signIn);
    }
  }, [isLoaded, userId, router]);

  useEffect(() => {
    if (!isLoaded || !userId || !user) return;
    if (isSuperAdmin(user.role) && pathname === ROUTES.dashboard) {
      router.replace(ROUTES.admin);
    }
  }, [isLoaded, userId, user, pathname, router]);

  if (!mounted || !isLoaded) {
    return <DashboardBootLoading message="Loading workspace..." />;
  }

  if (!userId) {
    return <DashboardBootLoading message="Signing in..." />;
  }

  return (
    <div className="flex min-h-screen">
      <Suspense fallback={<SidebarSkeleton />}>
        <Sidebar />
      </Suspense>
      <MobileNav />
      <div className="flex flex-1 flex-col lg:pl-64">
        <Header />
        <main className="flex-1 p-4 md:p-6 lg:p-8">{children}</main>
      </div>
      <Toaster />
    </div>
  );
}

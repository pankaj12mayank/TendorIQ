'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

import { useCurrentUser } from '@/hooks/use-auth';
import { getMembershipRole } from '@/lib/auth-user';
import { hasPermission, isSuperAdmin } from '@/lib/permissions';
import { LoadingState } from '@/components/ui/loading-state';

export default function AnalyticsPage() {
  const user = useCurrentUser();
  const router = useRouter();

  useEffect(() => {
    if (!user) return;
    if (isSuperAdmin(user.role)) {
      router.replace('/dashboard/admin?module=analytics');
      return;
    }
    const role = getMembershipRole(user);
    if (hasPermission(role, 'analytics:view', user.permissions)) {
      router.replace('/dashboard/usage');
      return;
    }
    router.replace('/dashboard');
  }, [user, router]);

  return (
    <div className="flex min-h-[40vh] items-center justify-center">
      <LoadingState message="Opening analytics..." />
    </div>
  );
}

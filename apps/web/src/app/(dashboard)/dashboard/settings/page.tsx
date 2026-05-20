'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

import { useCurrentUser } from '@/hooks/use-auth';
import { isSuperAdmin } from '@/lib/permissions';
import { LoadingState } from '@/components/ui/loading-state';

export default function SettingsPage() {
  const user = useCurrentUser();
  const router = useRouter();

  useEffect(() => {
    if (!user) return;
    if (isSuperAdmin(user.role)) {
      router.replace('/dashboard/admin?module=ai_settings');
    } else {
      router.replace('/dashboard/settings/profile');
    }
  }, [user, router]);

  return (
    <div className="flex min-h-[40vh] items-center justify-center">
      <LoadingState message="Opening settings..." />
    </div>
  );
}

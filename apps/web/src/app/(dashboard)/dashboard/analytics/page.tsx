'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { BarChart3, ArrowRight } from 'lucide-react';

import { useCurrentUser } from '@/hooks/use-auth';
import { isSuperAdmin } from '@/lib/permissions';
import { ROUTES } from '@/lib/routes';
import { LoadingState } from '@/components/ui/loading-state';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function AnalyticsPage() {
  const user = useCurrentUser();
  const router = useRouter();

  useEffect(() => {
    if (!user) return;
    if (isSuperAdmin(user.role)) {
      router.replace('/dashboard/admin?module=analytics');
    }
  }, [user, router]);

  if (!user) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <LoadingState message="Loading analytics..." />
      </div>
    );
  }

  if (isSuperAdmin(user.role)) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <LoadingState message="Opening platform analytics..." />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
        <p className="text-muted-foreground">
          Workspace usage and activity for your organization.
        </p>
      </div>
      <Card>
        <CardHeader>
          <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
            <BarChart3 className="h-5 w-5" />
          </div>
          <CardTitle>Usage & limits</CardTitle>
          <CardDescription>
            View tender volume, bid activity, and plan quotas on the usage dashboard.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild>
            <Link href={ROUTES.usage}>
              Open usage dashboard
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

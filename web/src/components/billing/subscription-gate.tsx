'use client';

import Link from 'next/link';
import { AlertTriangle, Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { useCurrentUser } from '@/hooks/use-auth';
import { useSubscriptionAccess } from '@/hooks/use-subscription-access';
import { canAccessAdminConsole } from '@/lib/permissions';
import { settingsTabHref } from '@/lib/routes';

export function SubscriptionExpiredBanner() {
  const user = useCurrentUser();
  const { data: access, isLoading } = useSubscriptionAccess();

  if (canAccessAdminConsole(user?.role)) {
    return null;
  }

  if (isLoading || !access || access.can_use_system) {
    return null;
  }

  const title =
    access.plan === 'free' ? 'Active subscription required' : 'Your plan expired';

  return (
    <div
      role="alert"
      className="mb-4 flex flex-col gap-3 rounded-lg border border-destructive/40 bg-destructive/10 p-4 sm:flex-row sm:items-center sm:justify-between"
    >
      <div className="flex gap-3">
        <AlertTriangle className="h-5 w-5 shrink-0 text-destructive" />
        <div>
          <p className="font-medium text-destructive">{title}</p>
          <p className="text-sm text-muted-foreground">
            {access.reason || 'Buy a plan on Billing to upload, analyze, and export.'}
          </p>
        </div>
      </div>
      <Button asChild variant="destructive" size="sm" className="shrink-0">
        <Link href={settingsTabHref('billing')}>View plans</Link>
      </Button>
    </div>
  );
}

interface SubscriptionGateProps {
  children: React.ReactNode;
  allowWhenExpired?: boolean;
}

export function SubscriptionGate({ children, allowWhenExpired = false }: SubscriptionGateProps) {
  const user = useCurrentUser();
  const { data: access, isLoading, isError } = useSubscriptionAccess();
  const isOwner = canAccessAdminConsole(user?.role);

  if (isLoading || !user) {
    return (
      <div className="flex min-h-[32vh] items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" />
        <span className="text-sm">Checking subscription…</span>
      </div>
    );
  }

  if (isOwner) {
    return <>{children}</>;
  }

  if (allowWhenExpired) {
    return <>{children}</>;
  }

  if (isError || !access) {
    return (
      <div className="flex min-h-[40vh] flex-col items-center justify-center gap-4 rounded-lg border border-dashed p-8 text-center">
        <p className="text-sm text-muted-foreground">Could not verify subscription. Try again.</p>
        <Button asChild variant="outline" size="sm">
          <Link href={settingsTabHref('billing')}>Open Billing</Link>
        </Button>
      </div>
    );
  }

  if (!access.can_use_system) {
    return (
      <div className="flex min-h-[40vh] flex-col items-center justify-center gap-4 rounded-lg border border-dashed p-8 text-center">
        <AlertTriangle className="h-10 w-10 text-destructive" />
        <h2 className="text-lg font-semibold">
          {access.plan === 'free' ? 'Purchase a plan to continue' : 'Your plan expired'}
        </h2>
        <p className="max-w-md text-sm text-muted-foreground">
          {access.reason ||
            'Upload, analysis, proposals, and exports need an active monthly plan.'}
        </p>
        <Button asChild>
          <Link href={settingsTabHref('billing')}>View plans</Link>
        </Button>
      </div>
    );
  }

  return <>{children}</>;
}

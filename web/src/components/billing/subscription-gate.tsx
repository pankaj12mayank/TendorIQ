'use client';

import Link from 'next/link';
import { AlertTriangle } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { useSubscriptionAccess } from '@/hooks/use-subscription-access';
import { settingsTabHref } from '@/lib/routes';

export function SubscriptionExpiredBanner() {
  const { data: access } = useSubscriptionAccess();

  if (!access?.is_expired || access.can_use_system) {
    return null;
  }

  return (
    <div
      role="alert"
      className="mb-4 flex flex-col gap-3 rounded-lg border border-destructive/40 bg-destructive/10 p-4 sm:flex-row sm:items-center sm:justify-between"
    >
      <div className="flex gap-3">
        <AlertTriangle className="h-5 w-5 shrink-0 text-destructive" />
        <div>
          <p className="font-medium text-destructive">Plan expired — read-only access</p>
          <p className="text-sm text-muted-foreground">
            {access.reason || 'Renew or upgrade your plan to upload, analyze, and export again.'}
          </p>
        </div>
      </div>
      <Button asChild variant="destructive" size="sm" className="shrink-0">
        <Link href={settingsTabHref('billing')}>Upgrade plan</Link>
      </Button>
    </div>
  );
}

interface SubscriptionGateProps {
  children: React.ReactNode;
  /** Allow billing/settings UI even when expired */
  allowWhenExpired?: boolean;
}

export function SubscriptionGate({ children, allowWhenExpired = false }: SubscriptionGateProps) {
  const { data: access, isLoading } = useSubscriptionAccess();

  if (allowWhenExpired || isLoading || !access || access.can_use_system) {
    return <>{children}</>;
  }

  return (
    <div className="flex min-h-[40vh] flex-col items-center justify-center gap-4 rounded-lg border border-dashed p-8 text-center">
      <AlertTriangle className="h-10 w-10 text-destructive" />
      <h2 className="text-lg font-semibold">Your plan has expired</h2>
      <p className="max-w-md text-sm text-muted-foreground">
        {access.reason || 'You can still sign in, but product features are paused until you renew.'}
      </p>
      <Button asChild>
        <Link href={settingsTabHref('billing')}>Go to Billing</Link>
      </Button>
    </div>
  );
}

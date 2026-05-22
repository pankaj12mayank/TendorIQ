'use client';

import { Info } from 'lucide-react';

/**
 * Super-admin console is platform-scoped. Tenant tender APIs require a tenant membership.
 */
export function PlatformScopeBanner() {
  return (
    <div
      role="status"
      className="mb-4 flex gap-3 rounded-lg border border-border bg-muted/40 px-4 py-3 text-sm text-muted-foreground"
    >
      <Info className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
      <p>
        Platform console metrics and user management are global. To work on tenders and documents,
        sign in with a tenant account or assign this user to an organization — tenant APIs require{' '}
        <code className="rounded bg-muted px-1 text-xs">X-Tenant-ID</code>.
      </p>
    </div>
  );
}

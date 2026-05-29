'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { FlaskConical, Shield } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { useCurrentUser } from '@/hooks/use-auth';
import { isCustomerWorkspacePath } from '@/lib/customer-workspace';
import { canAccessAdminConsole } from '@/lib/permissions';
import { ROUTES } from '@/lib/routes';

/** Shown when platform owner uses customer Upload / Analysis / etc. to verify the product. */
export function OwnerCustomerTestBanner() {
  const user = useCurrentUser();
  const pathname = usePathname();

  if (!user || !canAccessAdminConsole(user.role) || !isCustomerWorkspacePath(pathname)) {
    return null;
  }

  return (
    <div
      role="status"
      className="mb-4 flex flex-col gap-3 rounded-lg border border-primary/30 bg-primary/5 p-4 sm:flex-row sm:items-center sm:justify-between"
    >
      <div className="flex gap-3">
        <FlaskConical className="h-5 w-5 shrink-0 text-primary" />
        <div>
          <p className="font-medium text-foreground">Owner test mode — customer workspace</p>
          <p className="text-sm text-muted-foreground">
            You are previewing what paying customers see. Real users must purchase a plan on
            Billing before upload and export work for them.
          </p>
        </div>
      </div>
      <Button asChild variant="outline" size="sm" className="shrink-0 gap-2">
        <Link href={ROUTES.admin}>
          <Shield className="h-4 w-4" />
          Back to Admin
        </Link>
      </Button>
    </div>
  );
}

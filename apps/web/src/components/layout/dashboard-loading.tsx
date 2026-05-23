import { Skeleton } from '@/components/design-system/skeleton';
import { LoadingState } from '@/components/ui/loading-state';
import { cn } from '@/lib/utils';

export function SidebarSkeleton({ collapsed = false }: { collapsed?: boolean }) {
  return (
    <aside
      className={cn(
        'hidden lg:flex flex-col border-r border-border/80 bg-card/50',
        collapsed ? 'w-[var(--sidebar-collapsed)]' : 'w-[var(--sidebar-width)]'
      )}
      aria-hidden
    >
      <div className="flex h-16 items-center border-b px-4">
        <Skeleton className="h-6 w-28" />
      </div>
      <nav className="flex-1 space-y-4 p-3">
        {Array.from({ length: 4 }).map((_, g) => (
          <div key={g} className="space-y-2">
            <Skeleton className="mx-3 h-3 w-16" />
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full rounded-lg" />
            ))}
          </div>
        ))}
      </nav>
    </aside>
  );
}

export function DashboardBootLoading({ message }: { message: string }) {
  return (
    <div className="flex min-h-screen">
      <SidebarSkeleton />
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex h-16 items-center justify-end gap-2 border-b px-6">
          <Skeleton className="h-9 w-9 rounded-full" />
        </div>
        <div className="flex flex-1 items-center justify-center p-8">
          <LoadingState message={message} />
        </div>
      </div>
    </div>
  );
}

export function GuardLoadingPlaceholder({ className }: { className?: string }) {
  return (
    <span
      className={cn('inline-block h-9 min-w-[7rem] animate-pulse rounded-md bg-muted', className)}
      aria-busy="true"
      aria-label="Loading"
    />
  );
}

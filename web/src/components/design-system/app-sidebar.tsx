'use client';

import Link from 'next/link';
import { usePathname, useSearchParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, LayoutDashboard, Sparkles } from 'lucide-react';
import { useState } from 'react';

import { sidebarLayoutTransition } from '@/design-system/motion';
import { useReducedMotion } from '@/lib/use-reduced-motion';
import { cn } from '@/lib/utils';
import { useCurrentUser } from '@/hooks/use-auth';
import { getNavGroupsForUser } from '@/lib/nav-role';
import { useTenantStore } from '@/stores/tenant-store';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

export function AppSidebar() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const user = useCurrentUser();
  const groups = getNavGroupsForUser(user);
  const currentOrganization = useTenantStore((s) => s.currentOrganization);
  const [collapsed, setCollapsed] = useState(false);
  const reducedMotion = useReducedMotion();
  const layoutTransition = sidebarLayoutTransition(reducedMotion);

  const initials =
    user?.name
      ?.split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2) ?? 'U';

  return (
    <aside
      className={cn(
        'sidebar-panel fixed inset-y-0 left-0 z-sticky hidden flex-col transition-all duration-300 ease-premium lg:flex',
        collapsed ? 'w-[var(--sidebar-collapsed)]' : 'w-[var(--sidebar-width)]'
      )}
    >
      <div className="flex h-[4.25rem] items-center justify-between gap-2 border-b border-border/60 px-4">
        <Link
          href="/dashboard"
          className={cn('flex items-center gap-2.5 min-w-0', collapsed && 'justify-center w-full')}
        >
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
            <LayoutDashboard className="h-4 w-4" />
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <span className="font-display block text-base font-semibold tracking-tight text-gradient-cinematic-accent">
                TenderIQ
              </span>
              <span className="block truncate text-[10px] text-muted-foreground">Procurement AI</span>
            </div>
          )}
        </Link>
        {!collapsed && (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 shrink-0 text-muted-foreground"
            onClick={() => setCollapsed(true)}
            aria-label="Collapse sidebar"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
        )}
        {collapsed && (
          <Button
            variant="ghost"
            size="icon"
            className="absolute -right-3 top-20 z-10 h-6 w-6 rounded-full border bg-card shadow-sm"
            onClick={() => setCollapsed(false)}
            aria-label="Expand sidebar"
          >
            <ChevronLeft className="h-3 w-3 rotate-180" />
          </Button>
        )}
      </div>

      <nav className="flex-1 space-y-7 overflow-x-hidden overflow-y-auto scroll-premium px-3 py-5">
        {groups.map((group) => (
          <div key={group.label}>
            {!collapsed && (
              <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground/80">
                {group.label}
              </p>
            )}
            <ul className="space-y-1">
              {group.items.map((item) => {
                const [baseHref, query] = item.href.split('?');
                const moduleParam = query
                  ? new URLSearchParams(query).get('module')
                  : null;
                const isActive = moduleParam
                  ? pathname.startsWith('/dashboard/admin') &&
                    searchParams.get('module') === moduleParam
                  : baseHref === '/dashboard'
                    ? pathname === '/dashboard'
                    : baseHref === '/dashboard/admin'
                      ? pathname === '/dashboard/admin'
                      : pathname === baseHref || pathname.startsWith(`${baseHref}/`);
                const Icon = item.icon;
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={cn(
                        'nav-link',
                        isActive && 'nav-link-active',
                        collapsed && 'justify-center px-2.5'
                      )}
                      aria-current={isActive ? 'page' : undefined}
                      title={collapsed ? item.name : undefined}
                    >
                      {isActive && !collapsed && (
                        <motion.span
                          layoutId={reducedMotion ? undefined : 'sidebar-active'}
                          className="absolute inset-0 rounded-lg bg-primary"
                          transition={layoutTransition}
                        />
                      )}
                      <Icon
                        className={cn(
                          'relative z-10 h-4 w-4 shrink-0',
                          isActive && 'text-primary-foreground'
                        )}
                      />
                      {!collapsed && <span className="relative z-10">{item.name}</span>}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="border-t border-border/60 p-3">
        <AnimatePresence mode="wait">
          {!collapsed ? (
            <motion.div
              key="expanded"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-3"
            >
              <div className="flex items-center gap-3 rounded-xl border border-border/60 bg-muted/30 p-3">
                <Avatar className="h-9 w-9 ring-2 ring-primary/20">
                  <AvatarFallback className="bg-primary/15 text-xs font-semibold text-primary">
                    {initials}
                  </AvatarFallback>
                </Avatar>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{user?.name ?? 'User'}</p>
                  <p className="truncate text-xs text-muted-foreground">{user?.email}</p>
                </div>
              </div>
              <div className="rounded-xl border border-primary/15 bg-gradient-to-br from-primary/8 via-transparent to-info/10 px-3 py-2.5">
                <div className="flex items-center gap-2 text-primary">
                  <Sparkles className="h-3.5 w-3.5" />
                  <span className="text-[10px] font-semibold uppercase tracking-wider">AI ready</span>
                </div>
                <p className="mt-1 truncate text-xs font-medium">
                  {currentOrganization?.name ?? 'Your workspace'}
                </p>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="collapsed"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex justify-center py-1"
            >
              <Avatar className="h-9 w-9">
                <AvatarFallback className="bg-primary/15 text-xs font-semibold text-primary">
                  {initials}
                </AvatarFallback>
              </Avatar>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </aside>
  );
}

'use client';

import Link from 'next/link';
import { usePathname, useSearchParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, Sparkles } from 'lucide-react';
import { useState } from 'react';

import { roleNavGroups } from '@/design-system/icons';
import type { AppRole } from '@/design-system/tokens';
import { cn } from '@/lib/utils';
import { useCurrentUser } from '@/hooks/use-auth';
import { useTenantStore } from '@/stores/tenant-store';
import { Button } from '@/components/ui/button';

function resolveRole(role?: string): AppRole {
  if (role === 'super_admin') return 'super_admin';
  if (role === 'tenant_admin' || role === 'admin' || role === 'owner') return 'tenant_admin';
  return 'user';
}

export function AppSidebar() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const user = useCurrentUser();
  const role = resolveRole(user?.role);
  const groups = roleNavGroups[role];
  const currentOrganization = useTenantStore((s) => s.currentOrganization);
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        'hidden lg:flex flex-col border-r border-border/80 bg-card/50 backdrop-blur-xl transition-all duration-300 ease-premium',
        collapsed ? 'w-[var(--sidebar-collapsed)]' : 'w-[var(--sidebar-width)]'
      )}
    >
      <div className="flex h-16 items-center justify-between border-b border-border/60 px-4">
        {!collapsed && (
          <Link href="/dashboard" className="font-display text-lg font-semibold tracking-tight">
            <span className="text-gradient-brand">TenderIQ</span>
          </Link>
        )}
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 shrink-0"
          onClick={() => setCollapsed(!collapsed)}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          <ChevronLeft className={cn('h-4 w-4 transition-transform', collapsed && 'rotate-180')} />
        </Button>
      </div>

      <nav className="flex-1 space-y-6 overflow-y-auto scroll-premium p-3">
        {groups.map((group) => (
          <div key={group.label}>
            {!collapsed && (
              <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                {group.label}
              </p>
            )}
            <ul className="space-y-0.5">
              {group.items.map((item) => {
                const [baseHref, query] = item.href.split('?');
                const moduleParam = query
                  ? new URLSearchParams(query).get('module')
                  : null;
                const isActive = moduleParam
                  ? pathname.startsWith('/dashboard/admin') &&
                    searchParams.get('module') === moduleParam
                  : pathname === baseHref ||
                    (baseHref !== '/dashboard' && pathname.startsWith(`${baseHref}/`));
                const Icon = item.icon;
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={cn(
                        'group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200',
                        isActive
                          ? 'bg-primary text-primary-foreground shadow-sm'
                          : 'text-muted-foreground hover:bg-accent hover:text-foreground',
                        collapsed && 'justify-center px-2'
                      )}
                      title={collapsed ? item.name : undefined}
                    >
                      {isActive && (
                        <motion.span
                          layoutId="sidebar-active"
                          className="absolute inset-0 rounded-lg bg-primary"
                          transition={{ type: 'spring', stiffness: 380, damping: 32 }}
                        />
                      )}
                      <Icon className={cn('relative z-10 h-4 w-4 shrink-0', isActive && 'text-primary-foreground')} />
                      {!collapsed && <span className="relative z-10">{item.name}</span>}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <AnimatePresence>
        {!collapsed && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="border-t border-border/60 p-3"
          >
            <div className="rounded-xl border border-primary/20 bg-gradient-to-br from-primary/10 to-info/5 p-4">
              <div className="flex items-center gap-2 text-primary">
                <Sparkles className="h-4 w-4" />
                <span className="text-xs font-semibold uppercase tracking-wide">AI Ready</span>
              </div>
              <p className="mt-2 text-sm font-medium">{currentOrganization?.name ?? 'Your workspace'}</p>
              <p className="text-xs text-muted-foreground">Procurement intelligence active</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </aside>
  );
}

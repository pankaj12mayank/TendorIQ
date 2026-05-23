'use client';

import Link from 'next/link';
import { usePathname, useSearchParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, Sparkles } from 'lucide-react';
import { useState } from 'react';

import { roleNavGroups } from '@/design-system/icons';
import { sidebarLayoutTransition } from '@/design-system/motion';
import type { AppRole } from '@/design-system/tokens';
import { useReducedMotion } from '@/lib/use-reduced-motion';
import { cn } from '@/lib/utils';
import { useCurrentUser } from '@/hooks/use-auth';
import { getMembershipRole } from '@/lib/auth-user';
import { isAppFeatureEnabled } from '@/lib/feature-flags';
import { hasPermission } from '@/lib/permissions';
import { useTenantStore } from '@/stores/tenant-store';
import { Button } from '@/components/ui/button';

/** Nav href → permission required (omit = visible to all authenticated tenant users). */
const NAV_ITEM_PERMISSIONS: Record<string, string | undefined> = {
  '/dashboard/upload': 'document:create',
  '/dashboard/organizations': 'org:read',
  '/dashboard/billing': 'settings:read',
  '/dashboard/usage': 'analytics:view',
  '/dashboard/settings': 'settings:read',
  '/dashboard/tenders/review': 'tender:read',
};

const NAV_ITEM_FEATURES: Record<string, 'advanced_analytics' | undefined> = {
  '/dashboard/analytics': 'advanced_analytics',
};

function resolveRole(membershipRole?: string, platformRole?: string): AppRole {
  if (platformRole === 'super_admin') return 'super_admin';
  const role = membershipRole ?? platformRole;
  if (role === 'tenant_admin' || role === 'admin' || role === 'owner') return 'tenant_admin';
  if (role === 'manager') return 'manager';
  if (role === 'analyst') return 'analyst';
  if (role === 'member') return 'member';
  if (role === 'viewer') return 'viewer';
  return 'user';
}

function canSeeNavItem(
  href: string,
  membershipRole: string,
  permissions?: string[]
): boolean {
  const base = href.split('?')[0] ?? href;
  const feature = NAV_ITEM_FEATURES[base];
  if (feature && !isAppFeatureEnabled(feature)) {
    return false;
  }
  const required = NAV_ITEM_PERMISSIONS[base];
  if (!required) return true;
  return hasPermission(membershipRole, required, permissions);
}

export function AppSidebar() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const user = useCurrentUser();
  const membershipRole = getMembershipRole(user);
  const role = resolveRole(membershipRole, user?.role);
  const groups = (roleNavGroups[role] ?? [])
    .map((group) => ({
      ...group,
      items: group.items.filter((item) =>
        canSeeNavItem(item.href, membershipRole, user?.permissions)
      ),
    }))
    .filter((group) => group.items.length > 0);
  const currentOrganization = useTenantStore((s) => s.currentOrganization);
  const [collapsed, setCollapsed] = useState(false);
  const reducedMotion = useReducedMotion();
  const layoutTransition = sidebarLayoutTransition(reducedMotion);

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
                          layoutId={reducedMotion ? undefined : 'sidebar-active'}
                          className="absolute inset-0 rounded-lg bg-primary"
                          transition={layoutTransition}
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

import type { LucideIcon } from 'lucide-react';

import { roleNavGroups } from '@/design-system/icons';
import type { AppRole } from '@/design-system/tokens';
import { isProductFeatureEnabled } from '@/lib/feature-flags';
import { hasPermission, isSuperAdmin } from '@/lib/permissions';
import type { AuthUser } from '@/lib/auth-session';
import { getMembershipRole } from '@/lib/auth-user';

/** Nav href → permission required (omit = visible to all authenticated users). */
const NAV_ITEM_PERMISSIONS: Record<string, string | undefined> = {
  '/dashboard/upload': 'document:create',
  '/dashboard/settings': 'settings:read',
};

/** Nav href → product feature flag. */
const NAV_ITEM_FEATURES = {
  '/dashboard/analysis': 'aiAnalysis',
  '/dashboard/proposal': 'aiAnalysis',
} as const;

export function resolveNavRole(membershipRole?: string, platformRole?: string): AppRole {
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
  platformRole?: string,
  permissions?: string[]
): boolean {
  const base = href.split('?')[0] ?? href;
  const feature = NAV_ITEM_FEATURES[base as keyof typeof NAV_ITEM_FEATURES];
  if (feature && !isProductFeatureEnabled(feature)) {
    return false;
  }
  if (isSuperAdmin(platformRole) || isSuperAdmin(membershipRole)) {
    return true;
  }
  const required = NAV_ITEM_PERMISSIONS[base];
  if (!required) return true;
  return hasPermission(membershipRole, required, permissions);
}

export type NavGroup = {
  label: string;
  items: { name: string; href: string; icon: LucideIcon }[];
};

export function getNavGroupsForUser(user?: AuthUser | null): NavGroup[] {
  if (!user) return [];
  const membershipRole = getMembershipRole(user);
  const role = resolveNavRole(membershipRole, user.role);
  return (roleNavGroups[role] ?? roleNavGroups.user)
    .map((group) => ({
      ...group,
      items: group.items.filter((item) =>
        canSeeNavItem(item.href, membershipRole, user.role, user.permissions)
      ),
    }))
    .filter((group) => group.items.length > 0);
}

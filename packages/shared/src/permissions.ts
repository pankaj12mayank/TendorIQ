/**
 * Canonical permission matrix — keep in sync with packages/shared/permissions.json
 * and apps/api/src/core/rbac.py (loads the same JSON).
 */

import matrix from '../permissions.json';

export type PermissionString = string;

export const PERMISSION_ALIASES: Record<string, string> = {
  'tender:write': 'tender:update',
  'bid:write': 'bid:update',
  'document:write': 'document:update',
  'org:write': 'org:update',
  'settings:write': 'settings:update',
};

export const ROLE_PERMISSIONS_MATRIX: Record<string, readonly string[]> = matrix as Record<
  string,
  readonly string[]
>;

const PLATFORM_SUPER_ADMIN = 'super_admin';

function effectiveRole(role?: string): string | undefined {
  if (!role) return undefined;
  const r = role.trim().toLowerCase();
  if (r === PLATFORM_SUPER_ADMIN) return PLATFORM_SUPER_ADMIN;
  if (r === 'tenant_admin') return 'admin';
  if (r === 'user') return 'member';
  return r;
}

export function normalizePermission(permission: string): string {
  return PERMISSION_ALIASES[permission] ?? permission;
}

/** All defined permission strings (union across roles). */
export function allPermissions(): string[] {
  const set = new Set<string>();
  for (const perms of Object.values(ROLE_PERMISSIONS_MATRIX)) {
    for (const p of perms) set.add(p);
  }
  return [...set].sort();
}

/**
 * Permissions for a role. Prefer `granted` from API `/auth/me` when present.
 */
export function getRolePermissions(
  role?: string,
  granted?: string[] | null
): string[] {
  if (granted && granted.length > 0) {
    return [...granted];
  }
  if (!role) return ['tender:read'];
  if (role === PLATFORM_SUPER_ADMIN) {
    return ['all', ...ROLE_PERMISSIONS_MATRIX.super_admin];
  }
  const key = effectiveRole(role);
  if (!key) return ['tender:read'];
  return [...(ROLE_PERMISSIONS_MATRIX[key] ?? ['tender:read'])];
}

export function hasPermission(
  role: string | undefined,
  required: string,
  granted?: string[] | null
): boolean {
  const perms = getRolePermissions(role, granted);
  const needed = normalizePermission(required);

  if (perms.includes('all')) return true;
  if (perms.includes(needed)) return true;
  if (perms.includes(required)) return true;

  const [resource] = needed.split(':');
  const wildcard = `${resource}:*`;
  if (perms.includes(wildcard)) return true;

  return false;
}

export function isSuperAdmin(role?: string): boolean {
  return role === PLATFORM_SUPER_ADMIN;
}

export function isTenantAdmin(role?: string): boolean {
  const r = effectiveRole(role);
  return r === 'admin' || r === 'owner';
}

/** TenderIQ Lite — minimal permission helpers. */

export type PermissionString =
  | 'all'
  | 'tender:read'
  | 'tender:write'
  | 'document:read'
  | 'document:write'
  | 'analysis:run'
  | 'proposal:run'
  | 'export:run'
  | 'billing:read';

export const PERMISSION_ALIASES: Record<string, PermissionString> = {
  'document:create': 'document:write',
  'settings:read': 'billing:read',
};

export const ROLE_PERMISSIONS_MATRIX: Record<string, PermissionString[]> = {
  super_admin: ['all'],
  owner: ['tender:read', 'tender:write', 'document:read', 'document:write', 'analysis:run', 'proposal:run', 'export:run', 'billing:read'],
  admin: ['tender:read', 'tender:write', 'document:read', 'document:write', 'analysis:run', 'proposal:run', 'export:run', 'billing:read'],
  manager: ['tender:read', 'tender:write', 'document:read', 'document:write', 'analysis:run', 'proposal:run', 'export:run', 'billing:read'],
  analyst: ['tender:read', 'document:read', 'document:write', 'analysis:run', 'proposal:run', 'export:run'],
  member: ['tender:read', 'document:read', 'analysis:run'],
  viewer: ['tender:read', 'document:read'],
};

export const allPermissions = Object.values(ROLE_PERMISSIONS_MATRIX).flat();

export function normalizePermission(p: string): PermissionString | undefined {
  return p as PermissionString;
}

export function getRolePermissions(role: string): PermissionString[] {
  if (role === 'super_admin') return ['all'];
  return ROLE_PERMISSIONS_MATRIX[role] ?? ROLE_PERMISSIONS_MATRIX.viewer;
}

export function hasPermission(
  role: string | undefined,
  permission: PermissionString | string,
  extraPermissions?: string[]
): boolean {
  if (!role) return false;
  const normalized =
    PERMISSION_ALIASES[permission] ?? (normalizePermission(permission) ?? permission);
  if (extraPermissions?.length) {
    if (extraPermissions.includes('all') || extraPermissions.includes(normalized)) {
      return true;
    }
  }
  const perms = getRolePermissions(role);
  if (perms.includes('all')) return true;
  return perms.includes(normalized as PermissionString);
}

export function isSuperAdmin(role?: string): boolean {
  return role === 'super_admin';
}

export function isTenantAdmin(role?: string): boolean {
  return role === 'owner' || role === 'admin';
}

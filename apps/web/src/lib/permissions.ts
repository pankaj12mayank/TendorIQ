/** Role helpers aligned with API rbac (super_admin | tenant roles). */

export type PlatformRole = 'super_admin' | 'admin' | 'manager' | 'analyst' | 'viewer' | 'user' | 'owner';

export function isSuperAdmin(role?: string): boolean {
  return role === 'super_admin';
}

export function isTenantAdmin(role?: string): boolean {
  return role === 'admin' || role === 'owner' || role === 'tenant_admin';
}

export function canAccessAdminConsole(role?: string): boolean {
  return isSuperAdmin(role);
}

export function canAccessTenantDashboard(role?: string): boolean {
  if (!role) return false;
  if (isSuperAdmin(role)) return false;
  return true;
}

export function getRolePermissions(role?: string): string[] {
  if (isSuperAdmin(role)) return ['all'];
  if (isTenantAdmin(role)) {
    return ['tender:read', 'tender:write', 'bid:read', 'bid:write', 'document:read', 'document:write', 'org:read', 'org:write', 'billing:read'];
  }
  if (role === 'manager') {
    return ['tender:read', 'tender:write', 'bid:read', 'bid:write', 'document:read', 'document:write'];
  }
  if (role === 'analyst') {
    return ['tender:read', 'bid:read', 'document:read', 'document:write'];
  }
  if (role === 'viewer') {
    return ['tender:read', 'bid:read', 'document:read'];
  }
  return ['tender:read'];
}

export function hasPermission(role: string | undefined, required: string): boolean {
  const perms = getRolePermissions(role);
  if (perms.includes('all')) return true;
  if (perms.includes(required)) return true;
  const [resource] = required.split(':');
  return perms.includes(`${resource}:*`);
}

export {
  allPermissions,
  getRolePermissions,
  hasPermission,
  isSuperAdmin,
  isTenantAdmin,
  normalizePermission,
  PERMISSION_ALIASES,
  ROLE_PERMISSIONS_MATRIX,
  type PermissionString,
} from '@/shared/permissions';

import { isSuperAdmin } from '@/shared/permissions';

export function canAccessAdminConsole(role?: string): boolean {
  return isSuperAdmin(role);
}

export function canAccessTenantDashboard(role?: string): boolean {
  if (!role) return false;
  if (isSuperAdmin(role)) return false;
  return true;
}

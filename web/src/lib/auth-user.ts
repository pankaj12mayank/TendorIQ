import type { AuthUser } from '@/lib/auth-session';
import { isSuperAdmin } from '@/shared/permissions';

/** Membership role used for RBAC matrix (not platform super_admin). */
export function getMembershipRole(user?: AuthUser | null): string {
  if (!user) return 'viewer';
  if (isSuperAdmin(user.role)) return 'super_admin';
  return user.membershipRole ?? user.role ?? 'viewer';
}

export function getTenantId(user?: AuthUser | null): string | undefined {
  return user?.tenantId ?? undefined;
}

/** Headers for API calls: Bearer token + optional X-Tenant-ID. */
export function buildApiAuthHeaders(token?: string | null, user?: AuthUser | null): HeadersInit {
  const headers: Record<string, string> = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const tenantId = user?.tenantId ?? undefined;
  if (tenantId) {
    headers['X-Tenant-ID'] = tenantId;
  }
  return headers;
}

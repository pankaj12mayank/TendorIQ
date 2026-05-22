const TENANT_MEMBERSHIP_ROLES = new Set([
  'owner',
  'admin',
  'tenant_admin',
  'manager',
  'analyst',
  'member',
  'viewer',
]);

/** Post-login route from JWT/API role — no per-role API keys. */
export function getPostLoginPath(role?: string): string {
  if (!role || role === 'user') return '/onboarding';
  if (role === 'super_admin') return '/dashboard/admin';
  if (TENANT_MEMBERSHIP_ROLES.has(role)) return '/dashboard';
  return '/onboarding';
}

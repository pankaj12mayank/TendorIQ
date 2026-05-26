const TENANT_MEMBERSHIP_ROLES = new Set([
  'owner',
  'admin',
  'tenant_admin',
  'manager',
  'analyst',
  'member',
  'viewer',
]);

/** Post-login route from JWT/API role — Lite MVP (no onboarding flow). */
export function getPostLoginPath(role?: string): string {
  if (role === 'super_admin') return '/dashboard/admin';
  return '/dashboard';
}

/** Post-login route from JWT/API role — no per-role API keys. */
export function getPostLoginPath(role?: string): string {
  if (role === 'super_admin') return '/dashboard/admin';
  if (role === 'admin' || role === 'manager' || role === 'analyst' || role === 'viewer') {
    return '/dashboard';
  }
  return '/onboarding';
}

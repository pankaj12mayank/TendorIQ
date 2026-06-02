import type { AuthUser } from '@/lib/auth-session';

/** Lite MVP: authenticated user id is sufficient (no org picker). */
export const TENANT_WORKSPACE_REQUIRED =
  'Sign in to use this feature.';

export function hasTenantWorkspace(user?: AuthUser | null): boolean {
  return Boolean(user?.id);
}

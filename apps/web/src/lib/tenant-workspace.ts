import type { AuthUser } from './auth-session';

export const TENANT_WORKSPACE_REQUIRED =
  'Your account is not linked to a workspace yet. Complete onboarding or sign in with a tenant user.';

export function hasTenantWorkspace(user: AuthUser | null | undefined): boolean {
  return Boolean(user?.tenantId?.trim());
}

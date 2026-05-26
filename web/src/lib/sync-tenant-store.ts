import type { AuthUser } from '@/lib/auth-session';
import { useTenantStore } from '@/stores/tenant-store';

/** Hydrate sidebar org label from /auth/me (does not clear existing saved org). */
export function syncTenantStoreFromUser(user: AuthUser | null): void {
  if (!user?.tenantId) return;

  const { currentOrganization, setCurrentOrganization } = useTenantStore.getState();
  if (currentOrganization?.id === user.tenantId && currentOrganization.name) {
    return;
  }

  const profile = user.companyProfile;
  const name =
    (typeof profile?.company_name === 'string' && profile.company_name.trim()) ||
    currentOrganization?.name ||
    user.name ||
    'Your workspace';

  setCurrentOrganization({
    id: user.tenantId,
    name,
    slug: 'workspace',
    role: 'owner',
  });
}

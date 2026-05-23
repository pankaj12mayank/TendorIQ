const SESSION_KEY = 'tenderiq_super_admin_tenant_view';

/** Super admins normally use /dashboard/admin; E2E and support can opt into tenant UI. */
export function activateSuperAdminTenantView(): void {
  if (typeof window === 'undefined') return;
  sessionStorage.setItem(SESSION_KEY, '1');
}

export function clearSuperAdminTenantView(): void {
  if (typeof window === 'undefined') return;
  sessionStorage.removeItem(SESSION_KEY);
}

export function isSuperAdminTenantViewActive(): boolean {
  if (typeof window === 'undefined') return false;
  if (process.env.NEXT_PUBLIC_E2E_TENANT_DASHBOARD === '1') return true;
  if (sessionStorage.getItem(SESSION_KEY) === '1') return true;
  const params = new URLSearchParams(window.location.search);
  if (params.get('tenant_view') === '1') {
    activateSuperAdminTenantView();
    return true;
  }
  return false;
}

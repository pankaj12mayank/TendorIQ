/**
 * Canonical dashboard and auth routes — use instead of string literals in nav/links.
 */
export const ROUTES = {
  home: '/',
  landing: '/',
  signIn: '/sign-in',
  signUp: '/sign-up',
  forgotPassword: '/forgot-password',
  resetPassword: '/reset-password',
  onboarding: '/onboarding',
  adminLogin: '/admin/login',
  adminLoginLegacy: '/admin/sign-in',
  dashboard: '/dashboard',
  tenders: '/dashboard/tenders',
  tenderNew: '/dashboard/tenders/new',
  tenderAnalysis: '/dashboard/tenders/analysis',
  tenderReview: '/dashboard/tenders/review',
  review: '/dashboard/tenders/review',
  reviewLegacy: '/dashboard/review',
  bids: '/dashboard/bids',
  upload: '/dashboard/upload',
  documents: '/dashboard/documents',
  analytics: '/dashboard/analytics',
  billing: '/dashboard/billing',
  usage: '/dashboard/usage',
  organizations: '/dashboard/organizations',
  notifications: '/dashboard/notifications',
  settings: '/dashboard/settings',
  settingsProfile: '/dashboard/settings/profile',
  admin: '/dashboard/admin',
} as const;

export type AppRoute = (typeof ROUTES)[keyof typeof ROUTES];

/** Paths that do not require authentication (marketing + auth bootstrap). */
export const PUBLIC_ROUTE_PREFIXES = [
  ROUTES.home,
  '/landing',
  ROUTES.signIn,
  ROUTES.signUp,
  ROUTES.forgotPassword,
  ROUTES.resetPassword,
  ROUTES.adminLogin,
  ROUTES.adminLoginLegacy,
] as const;

export function isPublicAppPath(pathname: string): boolean {
  if (pathname === ROUTES.home || pathname === '/landing') return true;
  return PUBLIC_ROUTE_PREFIXES.some(
    (prefix) => prefix !== ROUTES.home && (pathname === prefix || pathname.startsWith(`${prefix}/`))
  );
}

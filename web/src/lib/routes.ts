/**

 * TenderIQ Lite — canonical routes (9 app surfaces + auth).

 */

export const ROUTES = {

  home: '/',

  signIn: '/sign-in',

  signUp: '/sign-up',

  forgotPassword: '/forgot-password',

  resetPassword: '/reset-password',

  dashboard: '/dashboard',

  upload: '/dashboard/upload',

  analysis: '/dashboard/analysis',

  proposal: '/dashboard/proposal',

  settings: '/dashboard/settings',

  billing: '/dashboard/billing',

  admin: '/dashboard/admin',

} as const;



export type AppRoute = (typeof ROUTES)[keyof typeof ROUTES];



/** Marketing + auth (no session required). */

export const PUBLIC_ROUTE_PREFIXES = [

  ROUTES.home,

  ROUTES.signIn,

  ROUTES.signUp,

  ROUTES.forgotPassword,

  ROUTES.resetPassword,

] as const;



/** Allowed authenticated dashboard paths (Lite MVP). */

export const LITE_DASHBOARD_PATHS = [

  ROUTES.dashboard,

  ROUTES.upload,

  ROUTES.analysis,

  ROUTES.proposal,

  ROUTES.settings,

  ROUTES.admin,

] as const;



/** Legacy paths → canonical (Phase 9 route cleanup). */

export const LEGACY_DASHBOARD_REDIRECTS: Record<string, string> = {

  '/dashboard/billing': `${ROUTES.settings}?tab=billing`,

  '/dashboard/settings/profile': `${ROUTES.settings}?tab=account`,

  '/dashboard/settings/ai': `${ROUTES.settings}?tab=account`,

  '/dashboard/organizations': ROUTES.settings,

  '/dashboard/usage': ROUTES.settings,

  '/dashboard/analytics': ROUTES.dashboard,

  '/dashboard/tenders': ROUTES.upload,

  '/dashboard/tenders/review': ROUTES.analysis,

  '/dashboard/documents': ROUTES.upload,

  '/dashboard/onboarding': ROUTES.dashboard,

  '/onboarding': ROUTES.dashboard,

  '/landing': ROUTES.home,

};



const DEAD_PREFIXES = [

  '/dashboard/bids',

  '/dashboard/team',

  '/dashboard/integrations',

  '/admin/login',

  '/admin/sign-in',

];



export function isPublicAppPath(pathname: string): boolean {

  if (pathname === ROUTES.home) return true;

  return PUBLIC_ROUTE_PREFIXES.some(

    (prefix) => prefix !== ROUTES.home && (pathname === prefix || pathname.startsWith(`${prefix}/`))

  );

}



export function isLiteDashboardPath(pathname: string): boolean {

  if (pathname === ROUTES.dashboard) return true;

  return LITE_DASHBOARD_PATHS.some(

    (p) => p !== ROUTES.dashboard && (pathname === p || pathname.startsWith(`${p}/`))

  );

}



export function resolveLegacyDashboardRedirect(pathname: string): string | null {

  if (LEGACY_DASHBOARD_REDIRECTS[pathname]) {

    return LEGACY_DASHBOARD_REDIRECTS[pathname];

  }

  for (const [legacy, target] of Object.entries(LEGACY_DASHBOARD_REDIRECTS)) {

    if (pathname.startsWith(`${legacy}/`)) {

      return target;

    }

  }

  return null;

}



export function isDeadDashboardPath(pathname: string): boolean {

  return DEAD_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`));

}



export type SettingsTab = 'account' | 'billing';

export const SETTINGS_TABS: SettingsTab[] = ['account', 'billing'];



export function settingsTabHref(tab: SettingsTab): string {

  return `${ROUTES.settings}?tab=${tab}`;

}



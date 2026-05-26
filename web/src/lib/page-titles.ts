/** Human-readable titles for dashboard header breadcrumbs. */

const TITLES: Record<string, string> = {
  '/dashboard': 'Overview',
  '/dashboard/upload': 'Upload',
  '/dashboard/analysis': 'Analysis',
  '/dashboard/proposal': 'Proposal',
  '/dashboard/settings': 'Settings',
  '/dashboard/settings/profile': 'Profile',
  '/dashboard/settings/ai': 'AI settings',
  '/dashboard/admin': 'Platform admin',
  '/dashboard/billing': 'Billing',
};

export function getPageTitle(pathname: string): string {
  if (TITLES[pathname]) return TITLES[pathname];
  const match = Object.keys(TITLES)
    .filter((p) => p !== '/dashboard' && pathname.startsWith(p))
    .sort((a, b) => b.length - a.length)[0];
  return match ? TITLES[match] : 'Workspace';
}

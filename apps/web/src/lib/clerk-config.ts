const PLACEHOLDER_PATTERN = /placeholder|xxx|your_|changeme|example/i;

export function isClerkConfigured(): boolean {
  const key = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ?? '';
  if (!key || PLACEHOLDER_PATTERN.test(key)) {
    return false;
  }
  return /^pk_(test|live)_[A-Za-z0-9]+$/.test(key) && key.length > 24;
}

const PUBLIC_PATHS = ['/', '/landing'];

export function isPublicPath(pathname: string): boolean {
  if (PUBLIC_PATHS.includes(pathname)) return true;
  if (pathname.startsWith('/sign-in') || pathname.startsWith('/sign-up')) return true;
  if (pathname.startsWith('/forgot-password') || pathname.startsWith('/reset-password')) return true;
  if (pathname === '/admin/login') return true;
  return false;
}

export function isProtectedPath(pathname: string): boolean {
  return (
    pathname.startsWith('/dashboard') ||
    pathname.startsWith('/onboarding') ||
    (pathname.startsWith('/admin') && pathname !== '/admin/login')
  );
}

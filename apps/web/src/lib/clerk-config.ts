import { isClerkPublishableKeyConfigured } from '@/lib/clerk-env';

export function isClerkConfigured(): boolean {
  return isClerkPublishableKeyConfigured();
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
  return pathname.startsWith('/dashboard') || pathname.startsWith('/onboarding');
}

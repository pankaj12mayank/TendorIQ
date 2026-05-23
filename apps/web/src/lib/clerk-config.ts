import { isClerkPublishableKeyConfigured } from '@/lib/clerk-env';
import { isPublicAppPath } from '@/lib/routes';

export function isClerkConfigured(): boolean {
  return isClerkPublishableKeyConfigured();
}

export function isPublicPath(pathname: string): boolean {
  return isPublicAppPath(pathname);
}

export function isProtectedPath(pathname: string): boolean {
  return pathname.startsWith('/dashboard') || pathname.startsWith('/onboarding');
}

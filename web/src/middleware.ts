import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

import { isClerkPublishableKeyConfigured } from '@/lib/clerk-env';
import {
  isDeadDashboardPath,
  resolveLegacyDashboardRedirect,
  ROUTES,
} from '@/lib/routes';

const isPublicRoute = createRouteMatcher([
  '/',
  '/sign-in(.*)',
  '/sign-up(.*)',
  '/forgot-password(.*)',
  '/api/webhooks(.*)',
  '/_next(.*)',
  '/favicon.ico',
  '/api/health',
]);

const clerkEnabled = isClerkPublishableKeyConfigured();

function applyLiteRouteRules(request: NextRequest): NextResponse | null {
  const pathname = request.nextUrl.pathname;
  const legacy = resolveLegacyDashboardRedirect(pathname);
  if (legacy) {
    return NextResponse.redirect(new URL(legacy, request.url));
  }
  if (isDeadDashboardPath(pathname)) {
    return NextResponse.redirect(new URL(ROUTES.dashboard, request.url));
  }
  return null;
}

const clerkProtected = clerkMiddleware(async (auth, request) => {
  const redirected = applyLiteRouteRules(request);
  if (redirected) return redirected;

  if (!isPublicRoute(request)) {
    const hasLocalSession = Boolean(request.cookies.get('__session')?.value);
    if (!hasLocalSession) {
      await auth.protect();
    }
  }
});

function localPassthrough(request: NextRequest) {
  const redirected = applyLiteRouteRules(request);
  if (redirected) return redirected;
  return NextResponse.next();
}

export default clerkEnabled ? clerkProtected : localPassthrough;

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    '/(api|trpc)(.*)',
  ],
};

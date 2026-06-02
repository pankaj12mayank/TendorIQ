import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

import { isClerkPublishableKeyConfigured } from '@/lib/clerk-env';
import {
  isDeadDashboardPath,
  resolveLegacyDashboardRedirect,
  ROUTES,
} from '@/lib/routes';

const PUBLIC_ROUTES = [
  '/',
  '/sign-in',
  '/sign-up',
  '/forgot-password',
  '/reset-password',
  '/api/webhooks',
  '/_next',
  '/favicon.ico',
  '/api/health',
];

function isPublicRoute(pathname: string): boolean {
  return PUBLIC_ROUTES.some((route) => pathname === route || pathname.startsWith(route + '/'));
}

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

async function clerkProtected(request: NextRequest): Promise<NextResponse<unknown>> {
  const { clerkMiddleware: cm } = await import('@clerk/nextjs/server');
  const handler: (req: NextRequest) => NextResponse<unknown> = cm(
    (auth, req) => {
      const redirected = applyLiteRouteRules(req);
      if (redirected) return redirected;

      if (!isPublicRoute(req.nextUrl.pathname)) {
        const hasLocalSession = Boolean(req.cookies.get('__session')?.value);
        if (!hasLocalSession) {
          return Response.redirect(new URL('/sign-in', req.url));
        }
      }
      return NextResponse.next();
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  ) as any;
  return handler(request);
}

function localPassthrough(request: NextRequest) {
  const redirected = applyLiteRouteRules(request);
  if (redirected) return redirected;
  if (!isPublicRoute(request.nextUrl.pathname)) {
    const hasLocalSession = Boolean(request.cookies.get('__session')?.value);
    if (!hasLocalSession) {
      return Response.redirect(new URL('/sign-in', request.url));
    }
  }
  return NextResponse.next();
}

export default clerkEnabled ? clerkProtected : localPassthrough;

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    '/(api|trpc)(.*)',
  ],
};

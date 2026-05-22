import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

import { isClerkPublishableKeyConfigured } from '@/lib/clerk-env';

const isPublicRoute = createRouteMatcher([
  '/sign-in(.*)',
  '/sign-up(.*)',
  '/',
  '/admin/login(.*)',
  '/api/webhooks(.*)',
  '/_next(.*)',
  '/favicon.ico',
  '/api/health',
]);

const clerkEnabled = isClerkPublishableKeyConfigured();

const clerkProtected = clerkMiddleware(async (auth, request) => {
  if (!isPublicRoute(request)) {
    await auth.protect();
  }
});

/** When Clerk keys are absent, rely on client-side local JWT guards only. */
function localPassthrough(_request: NextRequest) {
  return NextResponse.next();
}

export default clerkEnabled ? clerkProtected : localPassthrough;

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    '/(api|trpc)(.*)',
  ],
};

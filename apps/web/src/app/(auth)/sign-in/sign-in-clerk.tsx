'use client';

import { SignIn, useUser, useSession } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import { exchangeClerkSession } from '@/lib/auth-api';
import { setStoredSession } from '@/lib/auth-session';
import { getPostLoginPath } from '@/lib/auth-redirect';
import { isSuperAdmin } from '@/lib/permissions';

/** Clerk SSO block on the unified sign-in page (no separate tenant login). */
export default function SignInClerk() {
  const { isSignedIn, user } = useUser();
  const { session } = useSession();
  const router = useRouter();
  const [redirecting, setRedirecting] = useState(false);

  useEffect(() => {
    if (!isSignedIn || redirecting || !user || !session) return;

    const finish = async () => {
      setRedirecting(true);
      try {
        const clerkToken = await session.getToken();
        if (!clerkToken) {
          router.push('/dashboard');
          return;
        }

        const exchanged = await exchangeClerkSession(clerkToken);
        const apiToken = exchanged?.token ?? clerkToken;
        const authUser = exchanged?.user;
        if (authUser) {
          setStoredSession(apiToken, authUser);
        }

        const role = authUser?.membershipRole ?? authUser?.role;
        if (role && isSuperAdmin(role)) {
          router.replace('/dashboard/admin');
          return;
        }

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const onboardingRes = await fetch(`${apiUrl}/api/v1/onboarding/status`, {
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${apiToken}`,
          },
        });
        if (onboardingRes.ok) {
          const data = await onboardingRes.json();
          if (!data.is_completed) {
            router.push('/onboarding');
            return;
          }
        }
      } catch {
        // fall through to dashboard
      }
      const role =
        user.publicMetadata?.membership_role ??
        user.publicMetadata?.role;
      router.push(getPostLoginPath(role as string | undefined));
    };

    void finish();
  }, [isSignedIn, user, session, router, redirecting]);

  return (
    <SignIn signUpUrl="/sign-up" routing="hash" />
  );
}

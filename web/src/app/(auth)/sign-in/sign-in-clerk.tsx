'use client';

import { SignIn, useUser, useSession } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import { exchangeClerkSession } from '@/lib/auth-api';
import { setStoredSession } from '@/lib/auth-session';
import { getPostLoginPath } from '@/lib/auth-redirect';

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
      } catch {
        router.push('/dashboard');
        return;
      }
      const role =
        user.publicMetadata?.membership_role ??
        user.publicMetadata?.role;
      router.push(getPostLoginPath(role as string | undefined));
    };

    void finish();
  }, [isSignedIn, user, session, router, redirecting]);

  return <SignIn signUpUrl="/sign-up" routing="hash" />;
}

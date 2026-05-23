import { redirect } from 'next/navigation';

import { ROUTES } from '@/lib/routes';

/** Legacy admin sign-in URL → unified sign-in. */
export default function AdminSignInRedirectPage() {
  redirect(ROUTES.signIn);
}

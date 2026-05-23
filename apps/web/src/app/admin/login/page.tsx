import { redirect } from 'next/navigation';

import { ROUTES } from '@/lib/routes';

/** Legacy URL — all users sign in at /sign-in */
export default function AdminLoginRedirectPage() {
  redirect(ROUTES.signIn);
}

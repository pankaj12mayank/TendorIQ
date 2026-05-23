import { redirect } from 'next/navigation';

import { ROUTES } from '@/lib/routes';

/** Legacy `/admin/login` — redirects to unified `/sign-in` (super admins → `/dashboard/admin`). */
export default function AdminLoginRedirectPage() {
  redirect(ROUTES.signIn);
}

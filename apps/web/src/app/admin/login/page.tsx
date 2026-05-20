import { redirect } from 'next/navigation';

/** Legacy URL — all users sign in at /sign-in */
export default function AdminLoginRedirectPage() {
  redirect('/sign-in');
}

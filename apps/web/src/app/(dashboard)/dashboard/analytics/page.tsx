import { redirect } from 'next/navigation';

export default function AnalyticsRedirectPage() {
  redirect('/dashboard/admin?module=analytics');
}

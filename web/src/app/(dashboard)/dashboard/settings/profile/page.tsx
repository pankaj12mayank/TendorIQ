import { redirect } from 'next/navigation';

import { ROUTES } from '@/lib/routes';

export default function LegacyProfileSettingsPage() {
  redirect(`${ROUTES.settings}?tab=profile`);
}

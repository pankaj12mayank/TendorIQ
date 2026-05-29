import { redirect } from 'next/navigation';

import { ROUTES } from '@/lib/routes';

export default function LegacyAiSettingsPage() {
  redirect(`${ROUTES.settings}?tab=account`);
}

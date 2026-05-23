import { redirect } from 'next/navigation';

import { ROUTES } from '@/lib/routes';

/** Legacy review URL → tender review workspace. */
export default function ReviewRedirectPage() {
  redirect(ROUTES.tenderReview);
}

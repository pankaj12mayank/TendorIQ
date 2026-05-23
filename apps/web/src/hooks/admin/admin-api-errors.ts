import { toast } from 'sonner';

import { ApiError } from '@/lib/api-client';

/** Surface API errors without throwing — keeps other admin tabs usable when one endpoint fails. */
export function reportAdminApiError(err: unknown, fallback: string): string {
  const msg = err instanceof ApiError ? err.message : err instanceof Error ? err.message : fallback;
  toast.error(msg);
  return msg;
}

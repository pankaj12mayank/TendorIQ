import { ROUTES } from '@/lib/routes';

/** Routes that belong to the customer (subscribed user) product experience. */
export const CUSTOMER_WORKSPACE_PATHS = [
  ROUTES.upload,
  ROUTES.analysis,
  ROUTES.proposal,
  ROUTES.settings,
] as const;

export function isCustomerWorkspacePath(pathname: string): boolean {
  return CUSTOMER_WORKSPACE_PATHS.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`)
  );
}

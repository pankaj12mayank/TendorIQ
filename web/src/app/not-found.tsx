import Link from 'next/link';

import { ROUTES } from '@/lib/routes';

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-6 text-center">
      <h1 className="text-4xl font-bold">404</h1>
      <p className="text-muted-foreground">Page not found</p>
      <div className="flex flex-wrap justify-center gap-3">
        <Link
          href={ROUTES.home}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          Go home
        </Link>
        <Link
          href={ROUTES.signIn}
          className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted"
        >
          Sign in
        </Link>
        <Link
          href={ROUTES.dashboard}
          className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted"
        >
          Dashboard
        </Link>
      </div>
    </div>
  );
}

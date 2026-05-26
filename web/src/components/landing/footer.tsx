'use client';

import Link from 'next/link';

export function Footer() {
  return (
    <footer className="border-t border-border bg-muted/30">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 px-4 py-6 sm:flex-row sm:px-6 lg:px-8">
        <Link href="/" className="text-lg font-bold">
          <span className="bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
            TenderIQ
          </span>
        </Link>
        <p className="text-center text-sm text-muted-foreground sm:text-right">
          © {new Date().getFullYear()} TenderIQ. All rights reserved.
        </p>
      </div>
    </footer>
  );
}

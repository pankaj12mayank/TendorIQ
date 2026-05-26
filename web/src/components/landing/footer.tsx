'use client';

import Link from 'next/link';

export function Footer() {
  return (
    <footer className="relative border-t border-white/10 bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-6 px-4 py-10 sm:flex-row sm:px-6 lg:px-8">
        <div className="text-center sm:text-left">
          <Link href="/" className="font-display text-xl font-semibold text-gradient-cinematic-accent">
            TenderIQ
          </Link>
          <p className="mt-2 max-w-xs text-sm text-muted-foreground">
            Procurement intelligence for modern teams.
          </p>
        </div>
        <div className="flex flex-wrap justify-center gap-6 text-sm text-muted-foreground">
          <a href="#features" className="transition hover:text-foreground">
            Features
          </a>
          <a href="#pricing" className="transition hover:text-foreground">
            Pricing
          </a>
          <Link href="/sign-in" className="transition hover:text-foreground">
            Sign in
          </Link>
        </div>
        <p className="text-center text-xs text-muted-foreground sm:text-right">
          © {new Date().getFullYear()} TenderIQ
        </p>
      </div>
    </footer>
  );
}

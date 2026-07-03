import Link from 'next/link';

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-2 font-bold text-xl">
          TenderIQ
        </Link>
        <nav className="flex items-center gap-6">
          <Link href="/#features" className="text-sm text-muted-foreground hover:text-foreground">Features</Link>
          <Link href="/#pricing" className="text-sm text-muted-foreground hover:text-foreground">Pricing</Link>
          <Link href="/#faq" className="text-sm text-muted-foreground hover:text-foreground">FAQ</Link>
          <Link href="/sign-in" className="text-sm font-medium">Sign in</Link>
          <Link href="/sign-up" className="text-sm font-medium rounded-lg bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90">Get started</Link>
        </nav>
      </div>
    </header>
  );
}
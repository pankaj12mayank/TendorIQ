import { UserButton, useUser } from '@clerk/nextjs';
import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-8">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold tracking-tight">TenderIQ</h1>
        <p className="text-muted-foreground text-lg">Tender Management Platform</p>
        <div className="flex gap-4 justify-center pt-4">
          <Link
            href="/tenders"
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Browse Tenders
          </Link>
          <Link
            href="/sign-in"
            className="px-4 py-2 border border-input bg-background rounded-md hover:bg-muted"
          >
            Sign In
          </Link>
        </div>
      </div>
    </main>
  );
}
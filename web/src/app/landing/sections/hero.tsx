import Link from 'next/link';

export function HeroSection() {
  return (
    <section className="w-full py-24 md:py-32">
      <div className="container mx-auto px-4 text-center">
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
          AI Procurement Platform
        </h1>
        <p className="mt-6 text-lg text-muted-foreground max-w-2xl mx-auto">
          Upload RFPs, extract risks and deadlines, and generate proposals in minutes.
        </p>
        <div className="mt-10 flex items-center justify-center gap-4">
          <Link href="/sign-up" className="rounded-lg bg-primary px-6 py-3 text-primary-foreground font-medium hover:bg-primary/90">
            Start Monthly Plan
          </Link>
          <Link href="#pricing" className="rounded-lg border px-6 py-3 font-medium hover:bg-muted/50">
            See pricing
          </Link>
        </div>
      </div>
    </section>
  );
}
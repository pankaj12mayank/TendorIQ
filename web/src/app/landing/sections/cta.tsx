import Link from 'next/link';

export function CtaSection() {
  return (
    <section className="w-full py-20 bg-primary/5">
      <div className="container mx-auto px-4 text-center">
        <h2 className="text-3xl font-bold mb-4">Ready to analyze your next tender?</h2>
        <Link href="/sign-up" className="inline-block rounded-lg bg-primary px-8 py-3 text-primary-foreground font-medium hover:bg-primary/90">
          Get started
        </Link>
      </div>
    </section>
  );
}
'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { Check, Loader2 } from 'lucide-react';

export function PricingSection() {
  const [plan, setPlan] = useState<Record<string, any> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/api/public/site');
        const json = await res.json();
        const p = json?.data?.pricing?.plans?.[0];
        if (p) setPlan(p);
      } catch { /* ignore */ }
      setLoading(false);
    })();
  }, []);

  return (
    <section id="pricing" className="w-full py-20 bg-muted/30">
      <div className="container mx-auto px-4 text-center">
        <h2 className="text-3xl font-bold mb-4">Simple pricing</h2>
        <p className="text-muted-foreground mb-10">Monthly subscription for procurement teams.</p>
        {loading ? (
          <div className="max-w-sm mx-auto space-y-4">
            <div className="flex items-center justify-center gap-2 text-muted-foreground"><Loader2 className="h-5 w-5 animate-spin" /><span className="text-sm">Loading pricing...</span></div>
          </div>
        ) : plan ? (
          <div className="max-w-sm mx-auto">
            <div className="rounded-xl border bg-card p-8 text-left">
              {plan.popular && (
                <span className="inline-block rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary mb-4">
                  Most popular
                </span>
              )}
              <h3 className="text-xl font-bold">{plan.name}</h3>
              <p className="text-sm text-muted-foreground mt-1">{plan.description}</p>
              <p className="mt-6">
                <span className="text-4xl font-bold">${plan.monthly_usd}</span>
                <span className="text-muted-foreground">/mo</span>
              </p>
              <ul className="mt-6 space-y-3">
                {(plan.features || []).map((f: string) => (
                  <li key={f} className="flex items-start gap-2 text-sm">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                    {f}
                  </li>
                ))}
              </ul>
              <Link href="/sign-up" className="mt-8 block w-full rounded-lg bg-primary px-6 py-3 text-center text-primary-foreground font-medium hover:bg-primary/90">
                Subscribe now
              </Link>
            </div>
          </div>
        ) : (
          <p className="text-muted-foreground">Pricing not available.</p>
        )}
      </div>
    </section>
  );
}
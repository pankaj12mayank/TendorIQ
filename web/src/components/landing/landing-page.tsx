'use client';

import { useAuth } from '@/hooks/use-auth';
import { useSiteContent } from '@/hooks/use-site-content';
import type { PublicSitePayload } from '@/lib/public-site';

import { Navbar } from './navbar';
import { HeroSection } from './hero-section';
import { SocialProof } from './social-proof';
import { FeaturesSection } from './features-section';
import { PricingSection } from './pricing-section';
import { TestimonialsSection } from './testimonials-section';
import { FAQSection } from './faq-section';
import { CTASection } from './cta-section';
import { Footer } from './footer';
import { LandingSkeleton } from './landing-skeleton';

export function LandingPage({ initialSite }: { initialSite?: PublicSitePayload | null }) {
  const { isSignedIn } = useAuth();
  const { content, loading } = useSiteContent(initialSite ?? undefined);
  const landing = content?.landing;

  if (loading && !content) {
    return <LandingSkeleton />;
  }

  return (
    <div className="min-h-screen bg-background dark:bg-background-dark">
      <Navbar isSignedIn={isSignedIn} />

      <main>
        <HeroSection content={landing?.hero} />
        <SocialProof content={landing?.social_proof} />
        <FeaturesSection items={landing?.features} />
        <PricingSection
          plans={
            content?.pricing?.plans as Array<{
              id: string;
              name: string;
              description?: string;
              monthly_inr?: number | null;
              yearly_inr?: number | null;
              popular?: boolean;
              contact_sales?: boolean;
              features?: string[];
            }>
          }
        />
        <TestimonialsSection items={landing?.testimonials} />
        <FAQSection items={landing?.faq} />
        <CTASection cta={landing?.cta} />
      </main>

      <Footer />
    </div>
  );
}

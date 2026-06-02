'use client';

import { useAuth } from '@/hooks/use-auth';
import { useSiteContent } from '@/hooks/use-site-content';
import type { PublicSitePayload } from '@/lib/public-site';
import { CinematicBackground } from '@/components/cinematic/cinematic-background';

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
import { WorkflowTutorialSection } from './workflow-tutorial-section';

export function LandingPage({ initialSite }: { initialSite?: PublicSitePayload | null }) {
  const { isSignedIn } = useAuth();
  const { content, loading } = useSiteContent(initialSite ?? undefined);
  const landing = content?.landing;
  const images = landing?.images;

  if (loading && !content) {
    return <LandingSkeleton />;
  }

  return (
    <div className="dark cinematic-landing">
      <CinematicBackground intensity="hero" className="fixed inset-0 z-0" />
      <div className="relative z-10">
        <Navbar isSignedIn={isSignedIn} branding={images} />

        <main>
          <HeroSection content={landing?.hero} />
          <SocialProof content={landing?.social_proof} trustStats={content?.trust_stats} />
          <FeaturesSection items={landing?.features} />
          <WorkflowTutorialSection content={landing?.workflow_tutorial} />
          <PricingSection
            plans={
              content?.pricing?.plans as Array<{
                id: string;
                name: string;
                description?: string;
                monthly_usd?: number | null;
                monthly_inr?: number | null;
                popular?: boolean;
                contact_sales?: boolean;
                features?: string[];
              }>
            }
            copy={landing?.pricing}
          />
          <TestimonialsSection items={landing?.customer_stories ?? landing?.testimonials} />
          <FAQSection items={landing?.faq} contact={landing?.contact} />
          <CTASection cta={landing?.cta} contact={landing?.contact} />
        </main>

        <Footer />
      </div>
    </div>
  );
}

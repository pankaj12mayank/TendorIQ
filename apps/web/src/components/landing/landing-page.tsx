'use client';

import { useAuth } from '@/hooks/use-auth';

import { Navbar } from './navbar';
import { HeroSection } from './hero-section';
import { SocialProof } from './social-proof';
import { FeaturesSection } from './features-section';
import { AIWorkflowSection } from './ai-workflow-section';
import { DemoPreviewSection } from './demo-preview-section';
import { PricingSection } from './pricing-section';
import { TestimonialsSection } from './testimonials-section';
import { FAQSection } from './faq-section';
import { CTASection } from './cta-section';
import { Footer } from './footer';

export function LandingPage() {
  const { isSignedIn } = useAuth();

  return (
    <div className="min-h-screen bg-background dark:bg-background-dark">
      <Navbar isSignedIn={isSignedIn} />

      <main>
        <HeroSection />
        <SocialProof />
        <FeaturesSection />
        <AIWorkflowSection />
        <DemoPreviewSection />
        <PricingSection />
        <TestimonialsSection />
        <FAQSection />
        <CTASection />
      </main>

      <Footer />
    </div>
  );
}

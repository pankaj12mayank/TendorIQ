'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/use-auth';
import { useTheme } from 'next-themes';
import { motion, AnimatePresence } from 'framer-motion';

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
import { LoadingScreen } from './loading-screen';
import { AdminContentProvider } from './providers/admin-content-provider';

export function LandingPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [mounted, setMounted] = useState(false);
  const { theme, setTheme } = useTheme();
  const { isLoaded, isSignedIn } = useAuth();

  useEffect(() => {
    setMounted(true);
    const timer = setTimeout(() => setIsLoading(false), 2000);
    return () => clearTimeout(timer);
  }, []);

  if (!mounted || isLoading || !isLoaded) {
    return <LoadingScreen />;
  }

  return (
    <AdminContentProvider>
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
    </AdminContentProvider>
  );
}
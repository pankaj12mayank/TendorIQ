import { HeroSection } from './sections/hero';
import { FeaturesSection } from './sections/features';
import { PricingSection } from './sections/pricing';
import { HowItWorksSection } from './sections/how-it-works';
import { FaqSection } from './sections/faq';
import { CtaSection } from './sections/cta';

export default function LandingPage() {
  return (
    <div>
      <HeroSection />
      <FeaturesSection />
      <HowItWorksSection />
      <PricingSection />
      <FaqSection />
      <CtaSection />
    </div>
  );
}
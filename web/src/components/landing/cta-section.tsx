'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { useCurrentUser } from '@/hooks/use-auth';
import { Button } from '@/components/ui/button';
import { ArrowRight, Calendar, Sparkles } from 'lucide-react';

type CtaContent = { headline?: string; button?: string };

export function CTASection({ cta }: { cta?: CtaContent }) {
  const [isLoaded, setIsLoaded] = useState(false);
  const router = useRouter();
  const user = useCurrentUser();

  useEffect(() => {
    setIsLoaded(true);
  }, []);

  const handleGetStarted = () => {
    if (user) {
      router.push('/dashboard');
    } else {
      router.push('/sign-in');
    }
  };

  return (
    <section id="contact" className="relative scroll-mt-24 border-t border-white/5 py-24 md:py-32">
      <div className="relative z-10 mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isLoaded ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.2 }}
          className="glass-panel-strong mx-auto p-10 md:p-14"
        >
        <p className="cinematic-eyebrow mb-6 inline-flex">
          <Sparkles className="h-3.5 w-3.5" />
          Start today
        </p>

        <motion.h2
          initial={{ opacity: 0, y: 30 }}
          animate={isLoaded ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.3 }}
          className="cinematic-heading"
        >
          <span className="text-gradient-cinematic">
            {cta?.headline?.split('\n')[0] ?? 'Ready to transform'}
          </span>
          <br />
          <span className="text-gradient-cinematic-accent">
            {cta?.headline?.split('\n')[1] ?? 'your tender process?'}
          </span>
        </motion.h2>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={isLoaded ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.4 }}
          className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10"
        >
          Join 500+ companies already using TenderIQ to win more tenders, 
          reduce risk, and save time. Start your free trial today.
        </motion.p>

        {/* Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isLoaded ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.5 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Button 
              size="lg" 
              className="btn-cinematic h-12 px-8 text-base"
              onClick={handleGetStarted}
            >
              {cta?.button ?? 'Get Started'}
              <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
          </motion.div>

          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Button 
              size="lg" 
              variant="outline" 
              className="btn-cinematic-outline h-12 px-8 text-base"
            >
              <Calendar className="mr-2 w-5 h-5" />
              Schedule Demo
            </Button>
          </motion.div>
        </motion.div>

        {/* Trust Note */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={isLoaded ? { opacity: 1 } : {}}
          transition={{ delay: 0.7 }}
          className="mt-8 text-sm text-muted-foreground"
        >
          No credit card required • 14-day free trial • Cancel anytime
        </motion.p>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isLoaded ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.8 }}
          className="grid grid-cols-3 gap-8 mt-16 pt-16 border-t border-border/20"
        >
          {[
            { value: '500+', label: 'Companies' },
            { value: '$2B+', label: 'Tenders Processed' },
            { value: '99.9%', label: 'Uptime' },
          ].map((stat, index) => (
            <div key={stat.label}>
              <div className="text-2xl md:text-3xl font-bold">{stat.value}</div>
              <div className="text-sm text-muted-foreground">{stat.label}</div>
            </div>
          ))}
        </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
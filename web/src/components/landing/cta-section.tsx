'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { useCurrentUser } from '@/hooks/use-auth';
import { Button } from '@/components/ui/button';
import { ArrowRight, Mail, Sparkles } from 'lucide-react';

type CtaContent = { headline?: string; button?: string };
type ContactContent = { title?: string; support_email?: string };

export function CTASection({ cta, contact }: { cta?: CtaContent; contact?: ContactContent }) {
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
          Talk to our team
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
          Deploy a commercially reliable AI procurement workflow with secure yearly plans and owner-controlled CMS.
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

          <a
            href={`mailto:${contact?.support_email || 'support@tendoriq.com'}`}
            className="inline-flex items-center justify-center rounded-md border border-input bg-background px-6 py-3 text-sm font-medium shadow-sm transition-colors hover:bg-accent hover:text-accent-foreground"
          >
            <Mail className="mr-2 h-4 w-4" />
            {contact?.title || 'Talk to our team'}
          </a>
        </motion.div>

        </motion.div>
      </div>
    </section>
  );
}
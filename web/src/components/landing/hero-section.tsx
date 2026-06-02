'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { ArrowRight, Play, Sparkles } from 'lucide-react';

import { useCurrentUser } from '@/hooks/use-auth';
import { Button } from '@/components/ui/button';

type HeroContent = {
  headline?: string;
  subheadline?: string;
  cta_primary?: string;
  cta_secondary?: string;
};

export function HeroSection({ content }: { content?: HeroContent }) {
  const router = useRouter();
  const user = useCurrentUser();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setReady(true);
  }, []);

  const line1 = content?.headline?.split('\n')[0] ?? 'AI Procurement Platform';
  const line2 = content?.headline?.split('\n')[1] ?? '';

  const go = () => {
    if (user) {
      router.push(user.role === 'super_admin' ? '/dashboard/admin' : '/dashboard');
      return;
    }
    router.push('/sign-in');
  };

  return (
    <section id="home" className="relative scroll-mt-24 pt-28 pb-16 md:pt-36 md:pb-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-4xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={ready ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.1 }}
            className="mb-8 flex justify-center"
          >
            <span className="cinematic-eyebrow">
              <Sparkles className="h-3.5 w-3.5" />
              AI procurement platform
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 24 }}
            animate={ready ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.2, duration: 0.7 }}
            className="cinematic-headline-hero"
          >
            <span className="text-gradient-cinematic">{line1}</span>
            {line2 ? (
              <>
                <br />
                <span className="text-gradient-cinematic-accent">{line2}</span>
              </>
            ) : null}
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={ready ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.35 }}
            className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-muted-foreground md:text-xl"
          >
            {content?.subheadline ??
              'Upload RFPs, analyze with OpenAI, Anthropic, Gemini, or local Ollama — then export proposal-ready PDFs.'}
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={ready ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.45 }}
            className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row"
          >
            <Button size="lg" className="btn-cinematic h-12 px-8 text-base" onClick={go}>
              {content?.cta_primary ?? 'Open Dashboard'}
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="btn-cinematic-outline h-12 px-8 text-base"
              onClick={() => document.querySelector('#features')?.scrollIntoView({ behavior: 'smooth' })}
            >
              <Play className="mr-2 h-4 w-4" />
              {content?.cta_secondary ?? 'See features'}
            </Button>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={ready ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.55 }}
            className="mt-10"
          >
            <p className="text-center text-xs uppercase tracking-widest text-muted-foreground">
              Professional AI procurement platform
            </p>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

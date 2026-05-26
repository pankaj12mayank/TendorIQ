'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { ArrowRight, FileText, Play, Sparkles, Brain, Shield, Zap } from 'lucide-react';

import { useCurrentUser } from '@/hooks/use-auth';
import { Button } from '@/components/ui/button';

type HeroContent = {
  headline?: string;
  subheadline?: string;
  cta_primary?: string;
  cta_secondary?: string;
};

const stats = [
  { value: '70%', label: 'Time saved' },
  { value: '3×', label: 'More bids' },
  { value: '99%', label: 'Accuracy' },
  { value: '500+', label: 'Teams' },
];

export function HeroSection({ content }: { content?: HeroContent }) {
  const router = useRouter();
  const user = useCurrentUser();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setReady(true);
  }, []);

  const line1 = content?.headline?.split('\n')[0] ?? 'Win more tenders';
  const line2 = content?.headline?.split('\n')[1] ?? 'with cinematic AI';

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
            <br />
            <span className="text-gradient-cinematic-accent">{line2}</span>
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
              {content?.cta_primary ?? 'Get started'}
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
            className="mt-14 grid grid-cols-2 gap-6 md:grid-cols-4"
          >
            {stats.map((s, i) => (
              <div key={s.label} className="glass-panel px-4 py-5">
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={ready ? { opacity: 1, scale: 1 } : {}}
                  transition={{ delay: 0.6 + i * 0.05 }}
                >
                  <p className="font-display text-2xl font-bold tabular-nums md:text-3xl">{s.value}</p>
                  <p className="mt-1 text-xs uppercase tracking-wider text-muted-foreground">{s.label}</p>
                </motion.div>
              </div>
            ))}
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 48 }}
          animate={ready ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.65, duration: 0.9 }}
          className="relative mx-auto mt-16 max-w-5xl md:mt-20"
          style={{ perspective: '1200px' }}
        >
          <div className="absolute -inset-1 rounded-3xl bg-gradient-to-r from-primary/40 via-[hsl(var(--cinematic-accent))]/30 to-info/40 opacity-60 blur-2xl" />
          <motion.div
            animate={{ y: [0, -8, 0] }}
            transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
            className="glass-panel-strong relative overflow-hidden"
          >
            <div className="flex items-center gap-2 border-b border-white/10 bg-black/20 px-4 py-3">
              <div className="flex gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full bg-red-500/80" />
                <span className="h-2.5 w-2.5 rounded-full bg-amber-500/80" />
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-500/80" />
              </div>
              <span className="flex-1 text-center text-xs text-muted-foreground">app.tenderiq.com/dashboard</span>
            </div>
            <div className="grid gap-3 p-5 sm:grid-cols-2 lg:grid-cols-4">
              {[
                { icon: FileText, label: 'Active tenders', value: '24' },
                { icon: Brain, label: 'AI analyses', value: '156' },
                { icon: Shield, label: 'Risk flags', value: '3' },
                { icon: Zap, label: 'Completed', value: '89' },
              ].map((item) => (
                <div
                  key={item.label}
                  className="rounded-xl border border-white/5 bg-white/[0.03] p-4"
                >
                  <item.icon className="mb-2 h-5 w-5 text-primary" />
                  <p className="text-xl font-semibold tabular-nums">{item.value}</p>
                  <p className="text-xs text-muted-foreground">{item.label}</p>
                </div>
              ))}
            </div>
            <div className="space-y-2 border-t border-white/5 p-5">
              {['IT Infrastructure RFP', 'Office supplies 2026', 'Construction materials'].map((name, i) => (
                <div
                  key={name}
                  className="flex items-center gap-3 rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2.5"
                >
                  <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                  <span className="flex-1 truncate text-sm">{name}</span>
                  <span className="rounded-full bg-primary/15 px-2 py-0.5 text-[10px] font-medium text-primary">
                    {i === 0 ? 'Active' : i === 1 ? 'Done' : 'Review'}
                  </span>
                </div>
              ))}
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}

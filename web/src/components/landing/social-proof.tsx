'use client';

import { motion } from 'framer-motion';

const logos: Array<{ name: string; width: number }> = [];

type SocialProofContent = { tagline?: string; logos?: string[] };
type TrustStats = { companies?: number; tenders_processed?: number; success_rate?: number };

export function SocialProof({
  content,
  trustStats,
}: {
  content?: SocialProofContent;
  trustStats?: TrustStats;
}) {
  const tagline = content?.tagline ?? 'Trusted by industry leaders';
  const names =
    content?.logos && content.logos.length > 0
      ? content.logos.map((name) => ({ name, width: 120 }))
      : logos;
  return (
    <section className="py-20 bg-muted/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <p className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-4">
            {tagline}
          </p>
        </motion.div>

        {names.length ? (
          <div className="flex flex-wrap items-center justify-center gap-8 md:gap-16">
            {names.map((logo, index) => (
              <motion.div
                key={logo.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ scale: 1.03, opacity: 0.9 }}
                className="opacity-75 transition-all duration-300"
              >
                <div className="flex h-12 items-center justify-center" style={{ width: logo.width }}>
                  <span className="text-xl font-bold text-muted-foreground/60">{logo.name}</span>
                </div>
              </motion.div>
            ))}
          </div>
        ) : null}

        {/* Dynamic trust stats from backend */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.5 }}
          className="grid grid-cols-1 gap-8 mt-16 pt-16 border-t border-border sm:grid-cols-3"
        >
          {[
            { value: String(trustStats?.companies ?? 0), label: 'Companies' },
            { value: String(trustStats?.tenders_processed ?? 0), label: 'Tenders Processed' },
            { value: `${trustStats?.success_rate ?? 0}%`, label: 'Success Rate' },
          ].map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: 0.6 + index * 0.1 }}
              className="text-center"
            >
              <div className="text-3xl md:text-4xl font-bold text-foreground mb-2">
                {stat.value}
              </div>
              <div className="text-sm text-muted-foreground">{stat.label}</div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
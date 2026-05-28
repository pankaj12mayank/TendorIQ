'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Check, Sparkles, Building2, ArrowRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ROUTES } from '@/lib/routes';

const plans = [
  {
    id: 'starter',
    name: 'Starter',
    monthlyPrice: 29,
    description: 'Perfect for small teams getting started',
    icon: Sparkles,
    color: 'from-blue-500 to-cyan-500',
    features: [
      '5 Team Members',
      '100 Documents/month',
      'Basic AI Analysis',
      'Email Support',
      'Standard Analytics',
    ],
    notIncluded: ['Advanced Risk Detection', 'Proposal Generator', 'API Access'],
    cta: 'Get Started',
    popular: false,
  },
  {
    id: 'professional',
    name: 'Professional',
    monthlyPrice: 99,
    description: 'For growing teams with advanced needs',
    icon: Sparkles,
    color: 'from-purple-500 to-pink-500',
    features: [
      '20 Team Members',
      '500 Documents/month',
      'Advanced AI Analysis',
      'Risk Detection',
      'Proposal Generator',
      'Priority Support',
      'Advanced Analytics',
      'API Access',
    ],
    notIncluded: [],
    cta: 'Get Started',
    popular: true,
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    monthlyPrice: null,
    description: 'For large organizations with custom needs',
    icon: Building2,
    color: 'from-orange-500 to-red-500',
    features: [
      'Unlimited Team Members',
      'Unlimited Documents',
      'Full AI Suite',
      'Custom Integrations',
      'Dedicated Support',
      'Custom Training',
      'SLA Guarantee',
      'On-premise Option',
    ],
    notIncluded: [],
    cta: 'Contact Sales',
    popular: false,
  },
];

function getPlanDisplayPrice(
  monthlyPrice: number | null,
  opts?: { yearlyPrice?: number | null; currencyInr?: boolean }
): { price: string; period: string; sublabel?: string } {
  const sym = opts?.currencyInr ? '₹' : '$';
  if (monthlyPrice === null) {
    return { price: 'Custom', period: '' };
  }
  return {
    price: `${sym}${monthlyPrice}`,
    period: '/month',
    sublabel: `${sym}${monthlyPrice} billed monthly`,
  };
}

type AdminPlan = {
  id: string;
  name: string;
  description?: string;
  monthly_usd?: number | null;
  yearly_usd?: number | null;
  monthly_inr?: number | null;
  yearly_inr?: number | null;
  popular?: boolean;
  contact_sales?: boolean;
  features?: string[];
  active?: boolean;
};

function adminPlansToCards(adminPlans: AdminPlan[]) {
  return adminPlans.map((p) => ({
    id: p.id,
    name: p.name,
    monthlyPrice: p.monthly_usd ?? p.monthly_inr ?? null,
    yearlyPrice: p.yearly_usd ?? p.yearly_inr ?? null,
    description: p.description ?? '',
    icon: p.id === 'enterprise' ? Building2 : Sparkles,
    color: 'from-primary to-purple-500',
    features: p.features ?? [],
    notIncluded: [] as string[],
    cta: p.contact_sales ? 'Contact Sales' : 'Get Started',
    popular: Boolean(p.popular),
  }));
}

export function PricingSection({
  plans: adminPlans,
  copy,
}: {
  plans?: AdminPlan[];
  copy?: { title?: string; subtitle?: string; billing_note?: string };
}) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const router = useRouter();
  const displayPlans = (
    adminPlans && adminPlans.length > 0
      ? adminPlansToCards(adminPlans.filter((plan) => plan.active !== false))
      : plans
  ).slice(0, 1);

  const handlePlanSelect = (planId: string) => {
    if (planId === 'enterprise') {
      router.push(ROUTES.signIn);
    } else {
      router.push(ROUTES.signUp);
    }
  };

  return (
    <section id="pricing" className="relative scroll-mt-24 border-t border-white/5 py-24 md:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mx-auto mb-16 max-w-3xl text-center"
        >
          <div className="mb-6 inline-flex items-center gap-2 rounded-full bg-green-500/10 px-4 py-2 text-sm font-medium text-green-500">
            <Sparkles className="h-4 w-4" />
            Simple Pricing
          </div>
          <h2 className="mb-6 text-4xl font-bold md:text-5xl">
            {copy?.title ?? 'Plans That Scale With You'}
          </h2>
          <p className="mb-8 text-xl text-muted-foreground">
            {copy?.subtitle ?? 'Simple monthly subscriptions for procurement teams.'}
          </p>
          <p className="text-sm text-muted-foreground">Monthly plans only</p>
        </motion.div>

        <div className="mx-auto grid max-w-3xl gap-8 md:grid-cols-1">
          {displayPlans.map((plan, index) => {
            const highlighted = hoveredId ? plan.id === hoveredId : plan.popular;
            const display = getPlanDisplayPrice(plan.monthlyPrice, {
              currencyInr: false,
            });

            return (
              <motion.div
                key={plan.id}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                onMouseEnter={() => setHoveredId(plan.id)}
                onMouseLeave={() => setHoveredId(null)}
                className={cn(
                  'relative rounded-2xl p-8 transition-all duration-300',
                  highlighted
                    ? 'scale-[1.02] border-2 border-primary bg-gradient-to-b from-primary/15 to-background shadow-lg shadow-primary/20'
                    : 'border border-border bg-card dark:bg-card-dark'
                )}
              >
                {plan.popular && !hoveredId && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 rounded-full bg-primary px-4 py-1 text-sm font-medium text-primary-foreground">
                    Most Popular
                  </div>
                )}

                <div className="mb-6 text-center">
                  <div
                    className={cn(
                      'mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br',
                      plan.color
                    )}
                  >
                    <plan.icon className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="mb-2 text-xl font-bold">{plan.name}</h3>
                  <div className="flex flex-col items-center gap-1">
                    <div className="flex items-baseline justify-center gap-1">
                      <span className="text-4xl font-bold">{display.price}</span>
                      <span className="text-muted-foreground">{display.period}</span>
                    </div>
                    {display.sublabel && (
                      <p className="text-xs text-green-500">{display.sublabel}</p>
                    )}
                  </div>
                  <p className="mt-2 text-sm text-muted-foreground">{plan.description}</p>
                </div>

                <ul className="mb-8 space-y-3">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-3 text-sm">
                      <div className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/20">
                        <Check className="h-3 w-3 text-primary" />
                      </div>
                      {feature}
                    </li>
                  ))}
                  {plan.notIncluded.map((feature) => (
                    <li key={feature} className="flex items-center gap-3 text-sm text-muted-foreground/50">
                      <div className="flex h-5 w-5 items-center justify-center rounded-full bg-muted">
                        <span className="text-xs">×</span>
                      </div>
                      {feature}
                    </li>
                  ))}
                </ul>

                <Button
                  onClick={() => handlePlanSelect(plan.id)}
                  className={cn(
                    'w-full transition-all',
                    highlighted
                      ? 'bg-primary text-primary-foreground hover:bg-primary/90'
                      : 'bg-muted text-foreground hover:bg-muted/80'
                  )}
                >
                  {plan.cta}
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </motion.div>
            );
          })}
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mt-12 text-center"
        >
          {copy?.billing_note && <p className="mb-2 text-xs text-muted-foreground">{copy.billing_note}</p>}
          <p className="text-muted-foreground">
            Need a custom solution?{' '}
            <button
              type="button"
              className="font-medium text-primary hover:underline"
              onClick={() => router.push(ROUTES.signUp)}
            >
              Talk to our team
            </button>
          </p>
        </motion.div>
      </div>
    </section>
  );
}

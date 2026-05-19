'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { 
  Check, 
  Sparkles,
  Building2,
  ArrowRight
} from 'lucide-react';

const plans = [
  {
    id: 'starter',
    name: 'Starter',
    price: '$29',
    period: '/month',
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
    notIncluded: [
      'Advanced Risk Detection',
      'Proposal Generator',
      'API Access',
    ],
    cta: 'Start Free Trial',
    popular: false,
  },
  {
    id: 'professional',
    name: 'Professional',
    price: '$99',
    period: '/month',
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
    cta: 'Start Free Trial',
    popular: true,
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: 'Custom',
    period: '',
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

export function PricingSection() {
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'yearly'>('monthly');
  const router = useRouter();

  const handlePlanSelect = (planId: string) => {
    if (planId === 'enterprise') {
      router.push('/contact');
    } else {
      router.push('/onboarding');
    }
  };

  return (
    <section id="pricing" className="scroll-mt-24 py-32 bg-gradient-to-b from-background via-muted/10 to-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center max-w-3xl mx-auto mb-16"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-green-500/10 text-green-500 text-sm font-medium mb-6">
            <Sparkles className="w-4 h-4" />
            Simple Pricing
          </div>
          
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Plans That Scale With You
          </h2>
          
          <p className="text-xl text-muted-foreground mb-8">
            Start free, upgrade when you need more power.
          </p>

          {/* Billing Toggle */}
          <div className="inline-flex items-center p-1 bg-muted rounded-full">
            <button
              onClick={() => setBillingPeriod('monthly')}
              className={`px-6 py-2 rounded-full text-sm font-medium transition-all ${
                billingPeriod === 'monthly'
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-muted-foreground'
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingPeriod('yearly')}
              className={`px-6 py-2 rounded-full text-sm font-medium transition-all ${
                billingPeriod === 'yearly'
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-muted-foreground'
              }`}
            >
              Yearly
              <span className="ml-1 text-green-500 text-xs">-20%</span>
            </button>
          </div>
        </motion.div>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {plans.map((plan, index) => (
            <motion.div
              key={plan.id}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ y: -10 }}
              className={`relative rounded-2xl p-8 ${
                plan.popular
                  ? 'bg-gradient-to-b from-primary/10 to-background border-2 border-primary/50'
                  : 'bg-card dark:bg-card-dark border border-border'
              }`}
            >
              {/* Popular Badge */}
              {plan.popular && (
                <motion.div
                  initial={{ scale: 0 }}
                  whileInView={{ scale: 1 }}
                  className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-primary text-white text-sm font-medium rounded-full"
                >
                  Most Popular
                </motion.div>
              )}

              {/* Header */}
              <div className="text-center mb-6">
                <div className={`inline-flex w-12 h-12 rounded-xl bg-gradient-to-br ${plan.color} items-center justify-center mb-4`}>
                  <plan.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-bold mb-2">{plan.name}</h3>
                <div className="flex items-baseline justify-center gap-1">
                  <span className="text-4xl font-bold">{plan.price}</span>
                  <span className="text-muted-foreground">{plan.period}</span>
                </div>
                <p className="text-sm text-muted-foreground mt-2">{plan.description}</p>
              </div>

              {/* Features */}
              <ul className="space-y-3 mb-8">
                {plan.features.map((feature, i) => (
                  <motion.li
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.3 + i * 0.05 }}
                    className="flex items-center gap-3 text-sm"
                  >
                    <div className="w-5 h-5 rounded-full bg-primary/20 flex items-center justify-center">
                      <Check className="w-3 h-3 text-primary" />
                    </div>
                    {feature}
                  </motion.li>
                ))}
                {plan.notIncluded.map((feature, i) => (
                  <li key={i} className="flex items-center gap-3 text-sm text-muted-foreground/50">
                    <div className="w-5 h-5 rounded-full bg-muted flex items-center justify-center">
                      <span className="text-xs">×</span>
                    </div>
                    {feature}
                  </li>
                ))}
              </ul>

              {/* CTA */}
              <Button
                onClick={() => handlePlanSelect(plan.id)}
                className={`w-full ${
                  plan.popular
                    ? 'bg-primary hover:bg-primary/90'
                    : 'bg-muted hover:bg-muted/80'
                }`}
              >
                {plan.cta}
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </motion.div>
          ))}
        </div>

        {/* Comparison Note */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="text-center mt-12"
        >
          <p className="text-muted-foreground">
            Need a custom solution?{' '}
            <button className="text-primary font-medium hover:underline">
              Talk to our team
            </button>
          </p>
        </motion.div>
      </div>
    </section>
  );
}
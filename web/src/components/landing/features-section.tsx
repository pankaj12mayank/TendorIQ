'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  FileText, 
  Shield, 
  CheckSquare, 
  FileEdit, 
  BarChart3, 
  Users,
  ArrowRight,
  Zap,
  Brain,
  Database,
  Lock
} from 'lucide-react';

const features = [
  {
    icon: FileText,
    title: 'AI Document Extraction',
    description: 'Automatically extract key information from tender documents using advanced OCR and NLP.',
    color: 'from-blue-500 to-cyan-500',
  },
  {
    icon: Shield,
    title: 'Risk Detection',
    description: 'Identify potential risks and compliance issues before they become problems.',
    color: 'from-red-500 to-orange-500',
  },
  {
    icon: CheckSquare,
    title: 'Smart Checklists',
    description: 'Generate comprehensive compliance checklists tailored to each tender.',
    color: 'from-green-500 to-emerald-500',
  },
  {
    icon: FileEdit,
    title: 'Proposal Builder',
    description: 'Create winning proposals faster with AI-assisted content generation.',
    color: 'from-purple-500 to-pink-500',
  },
  {
    icon: BarChart3,
    title: 'Advanced Analytics',
    description: 'Track performance metrics and gain insights to improve your win rate.',
    color: 'from-indigo-500 to-violet-500',
  },
  {
    icon: Users,
    title: 'Team Collaboration',
    description: 'Work together seamlessly with role-based access and real-time updates.',
    color: 'from-teal-500 to-cyan-500',
  },
];

type FeatureItem = { title: string; description: string };

const iconCycle = [FileText, Shield, CheckSquare, FileEdit, BarChart3, Brain];

export function FeaturesSection({ items }: { items?: FeatureItem[] }) {
  const list =
    items && items.length > 0
      ? items.map((f, i) => ({
          icon: iconCycle[i % iconCycle.length],
          title: f.title,
          description: f.description,
          color: 'from-primary to-purple-500',
        }))
      : features;
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setIsLoaded(true);
        }
      },
      { threshold: 0.1 }
    );

    const section = document.getElementById('features');
    if (section) observer.observe(section);

    return () => observer.disconnect();
  }, []);

  return (
    <section id="features" className="relative scroll-mt-24 border-t border-white/5 py-24 md:py-32">
      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mx-auto mb-16 max-w-3xl text-center md:mb-20"
        >
          <p className="cinematic-eyebrow mb-6 inline-flex">
            <Zap className="h-3.5 w-3.5" />
            Powerful features
          </p>
          <h2 className="cinematic-heading">Everything you need to win tenders</h2>
          <p className="mt-4 text-lg text-muted-foreground">
            AI-powered tools for extraction, risk, proposals, and team workflow — in one cinematic workspace.
          </p>
        </motion.div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {list.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ y: -5 }}
              className="glass-panel group relative p-8 transition-all duration-300 hover:border-primary/40"
            >
              {/* Hover Glow */}
              <div className={`absolute inset-0 bg-gradient-to-br ${feature.color} opacity-0 group-hover:opacity-10 rounded-2xl transition-opacity duration-300`} />
              
              {/* Icon */}
              <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}>
                <feature.icon className="w-7 h-7 text-white" />
              </div>
              
              {/* Content */}
              <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
              <p className="text-muted-foreground mb-4">{feature.description}</p>
              
              {/* Learn More */}
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                whileHover={{ opacity: 1, x: 0 }}
                className="flex items-center text-primary text-sm font-medium cursor-pointer"
              >
                Learn more
                <ArrowRight className="w-4 h-4 ml-1" />
              </motion.div>
            </motion.div>
          ))}
        </div>

        {/* Feature Highlight Cards */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.4 }}
          className="grid md:grid-cols-3 gap-6 mt-16"
        >
          {[
            {
              icon: Brain,
              title: 'Neural Processing',
              desc: 'Advanced ML models trained on millions of tenders',
              stat: '99.7%',
            },
            {
              icon: Database,
              title: 'Smart Storage',
              desc: 'Secure document management with version control',
              stat: '∞',
            },
            {
              icon: Lock,
              title: 'Enterprise Security',
              desc: 'SOC 2 compliant with end-to-end encryption',
              stat: '256-bit',
            },
          ].map((item, index) => (
            <motion.div
              key={item.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.5 + index * 0.1 }}
              className="flex items-center gap-4 p-6 bg-muted/30 rounded-xl"
            >
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                <item.icon className="w-6 h-6 text-primary" />
              </div>
              <div className="flex-1">
                <div className="font-semibold">{item.title}</div>
                <div className="text-sm text-muted-foreground">{item.desc}</div>
              </div>
              <div className="text-2xl font-bold text-primary">{item.stat}</div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
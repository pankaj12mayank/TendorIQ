'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Minus, HelpCircle } from 'lucide-react';

const faqs = [
  {
    id: 1,
    question: 'How does AI extraction work?',
    answer: 'Our AI uses advanced OCR and NLP to analyze your tender documents. It automatically identifies key information like dates, requirements, deliverables, and compliance criteria. The system learns from millions of tenders to provide accurate extractions.',
  },
  {
    id: 2,
    question: 'Is my data secure?',
    answer: 'Absolutely. We use enterprise-grade encryption (AES-256) for all data at rest and TLS 1.3 for data in transit. We are SOC 2 Type II compliant and never share your data with third parties. You can also choose to host on-premise for complete control.',
  },
  {
    id: 3,
    question: 'Can I integrate with existing tools?',
    answer: 'Yes! We offer API access and native integrations with popular tools including Salesforce, SAP, Microsoft Dynamics, Slack, and more. Our team can help you build custom integrations for your specific needs.',
  },
  {
    id: 4,
    question: 'What happens if I exceed my plan limits?',
    answer: 'We never lock you out. If you exceed your plan limits, we\'ll notify you and you can either upgrade your plan or pay for overage at standard rates. You\'re always in control.',
  },
  {
    id: 5,
    question: 'How long does onboarding take?',
    answer: 'Most teams are up and running within 24 hours. Our intuitive interface requires minimal training, and we provide comprehensive documentation, video tutorials, and live onboarding support for enterprise customers.',
  },
  {
    id: 6,
    question: 'Do you offer a free trial?',
    answer: 'Yes! All plans come with a 14-day free trial. No credit card required. You get full access to all features so you can experience the platform before committing.',
  },
];

export function FAQSection() {
  const [openId, setOpenId] = useState<number | null>(null);

  const toggle = (id: number) => {
    setOpenId(openId === id ? null : id);
  };

  return (
    <section id="faq" className="scroll-mt-24 py-32 bg-gradient-to-b from-background to-muted/20">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-500/10 text-indigo-500 text-sm font-medium mb-6">
            <HelpCircle className="w-4 h-4" />
            FAQ
          </div>
          
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Frequently Asked Questions
          </h2>
          
          <p className="text-xl text-muted-foreground">
            Everything you need to know about TenderIQ.
          </p>
        </motion.div>

        {/* FAQ Items */}
        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <motion.div
              key={faq.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="bg-card dark:bg-card-dark border border-border rounded-xl overflow-hidden"
            >
              <button
                onClick={() => toggle(faq.id)}
                className="w-full flex items-center justify-between p-6 text-left"
              >
                <span className="font-semibold text-lg pr-4">{faq.question}</span>
                <motion.div
                  animate={{ rotate: openId === faq.id ? 180 : 0 }}
                  transition={{ duration: 0.3 }}
                  className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center"
                >
                  {openId === faq.id ? (
                    <Minus className="w-4 h-4" />
                  ) : (
                    <Plus className="w-4 h-4" />
                  )}
                </motion.div>
              </button>
              
              <AnimatePresence>
                {openId === faq.id && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3 }}
                    className="overflow-hidden"
                  >
                    <div className="px-6 pb-6">
                      <div className="h-px bg-border mb-4" />
                      <p className="text-muted-foreground leading-relaxed">
                        {faq.answer}
                      </p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>

        {/* Contact CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mt-12 text-center"
        >
          <p className="text-muted-foreground mb-4">
            Still have questions?
          </p>
          <button className="text-primary font-medium hover:underline">
            Contact our support team →
          </button>
        </motion.div>
      </div>
    </section>
  );
}
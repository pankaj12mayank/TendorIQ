'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Quote, Star, ChevronLeft, ChevronRight } from 'lucide-react';

type TestimonialItem = {
  quote: string;
  author: string;
  role?: string;
  company?: string;
};

export function TestimonialsSection({ items }: { items?: TestimonialItem[] }) {
  const slides =
    items && items.length > 0
      ? items.map((t, i) => ({
          id: i + 1,
          content: t.quote,
          author: t.author,
          role: t.role ?? '',
          company: t.company ?? '',
          avatar: t.author
            .split(' ')
            .map((w) => w[0])
            .join('')
            .slice(0, 2)
            .toUpperCase(),
          rating: 5,
        }))
      : [];
  const [activeIndex, setActiveIndex] = useState(0);
  if (!slides.length) return null;

  const handlePrev = () => {
    setActiveIndex((prev) => (prev - 1 + slides.length) % slides.length);
  };

  const handleNext = () => {
    setActiveIndex((prev) => (prev + 1) % slides.length);
  };

  return (
    <section id="testimonials" className="scroll-mt-24 py-32 bg-muted/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center max-w-3xl mx-auto mb-20"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-yellow-500/10 text-yellow-500 text-sm font-medium mb-6">
            <Star className="w-4 h-4" />
            Customer Stories
          </div>
          
          <h2 className="text-4xl md:text-5xl font-bold mb-6">Customer Stories</h2>
          
          <p className="text-xl text-muted-foreground">
            See what industry leaders are saying about TenderIQ.
          </p>
        </motion.div>

        {/* Testimonials Carousel */}
        <div className="relative max-w-4xl mx-auto">
          {/* Background Quote */}
          <div className="absolute -top-10 -left-10 text-[200px] text-primary/10 font-serif leading-none">
            <Quote className="w-48 h-48 -rotate-12" />
          </div>

          <AnimatePresence mode="wait">
            <motion.div
              key={activeIndex}
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -50 }}
              transition={{ duration: 0.5 }}
              className="relative bg-card dark:bg-card-dark border border-border rounded-2xl p-8 md:p-12"
            >
              {/* Stars */}
              <div className="flex gap-1 mb-6">
                {[...Array(slides[activeIndex].rating)].map((_, i) => (
                  <motion.div
                    key={i}
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.2 + i * 0.1 }}
                  >
                    <Star className="w-5 h-5 fill-yellow-500 text-yellow-500" />
                  </motion.div>
                ))}
              </div>

              {/* Content */}
              <p className="text-xl md:text-2xl text-foreground mb-8 leading-relaxed">
                "{slides[activeIndex].content}"
              </p>

              {/* Author */}
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-full bg-gradient-to-br from-primary to-purple-500 flex items-center justify-center text-white font-bold text-lg">
                  {slides[activeIndex].avatar}
                </div>
                <div>
                  <div className="font-semibold text-foreground">
                    {slides[activeIndex].author}
                  </div>
                  <div className="text-muted-foreground text-sm">
                    {slides[activeIndex].role}
                    {slides[activeIndex].company ? ` at ${slides[activeIndex].company}` : ''}
                  </div>
                </div>
              </div>
            </motion.div>
          </AnimatePresence>

          {/* Navigation */}
          <div className="flex items-center justify-center gap-4 mt-8">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={handlePrev}
              className="w-12 h-12 rounded-full border border-border flex items-center justify-center hover:bg-muted transition-colors"
            >
              <ChevronLeft className="w-5 h-5" />
            </motion.button>

            <div className="flex gap-2">
              {slides.map((_, index) => (
                <motion.button
                  key={index}
                  onClick={() => setActiveIndex(index)}
                  className={`w-2 h-2 rounded-full transition-all ${
                    index === activeIndex
                      ? 'w-8 bg-primary'
                      : 'bg-muted-foreground/30'
                  }`}
                />
              ))}
            </div>

            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={handleNext}
              className="w-12 h-12 rounded-full border border-border flex items-center justify-center hover:bg-muted transition-colors"
            >
              <ChevronRight className="w-5 h-5" />
            </motion.button>
          </div>
        </div>

        {/* CMS-provided stories only; no hardcoded company list */}
      </div>
    </section>
  );
}
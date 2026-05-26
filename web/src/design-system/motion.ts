/** Minimal motion tokens (Framer Motion optional). */

import type { Transition } from 'framer-motion';

export const fadeIn = {
  initial: { opacity: 0, y: 6 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.25 },
};

export const staggerContainer = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.06, delayChildren: 0.04 },
  },
};

export const staggerItem = {
  hidden: { opacity: 0, y: 10 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.22, 1, 0.36, 1] } },
};

export function sidebarLayoutTransition(reducedMotion?: boolean): Transition {
  if (reducedMotion) return { duration: 0 };
  return { duration: 0.2, ease: 'easeOut' };
}

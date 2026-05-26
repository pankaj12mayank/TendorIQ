'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

import { cn } from '@/lib/utils';

type CinematicBackgroundProps = {
  className?: string;
  intensity?: 'subtle' | 'medium' | 'hero';
  showGrid?: boolean;
  interactive?: boolean;
};

export function CinematicBackground({
  className,
  intensity = 'medium',
  showGrid = true,
  interactive = true,
}: CinematicBackgroundProps) {
  const [mouse, setMouse] = useState({ x: 50, y: 30 });

  useEffect(() => {
    if (!interactive) return;
    const onMove = (e: MouseEvent) => {
      setMouse({
        x: (e.clientX / window.innerWidth) * 100,
        y: (e.clientY / window.innerHeight) * 100,
      });
    };
    window.addEventListener('mousemove', onMove);
    return () => window.removeEventListener('mousemove', onMove);
  }, [interactive]);

  const orbScale = intensity === 'hero' ? 1 : intensity === 'medium' ? 0.75 : 0.5;

  return (
    <div className={cn('pointer-events-none absolute inset-0 overflow-hidden', className)} aria-hidden>
      <div className="cinematic-base-gradient absolute inset-0" />
      {showGrid && <div className="cinematic-grid absolute inset-0" />}
      <div className="cinematic-grain absolute inset-0 opacity-[0.35]" />
      <motion.div
        className="cinematic-orb cinematic-orb-primary absolute rounded-full"
        style={{
          width: `${24 * orbScale}rem`,
          height: `${24 * orbScale}rem`,
          left: `${mouse.x * 0.15}%`,
          top: `${mouse.y * 0.1}%`,
        }}
        animate={
          interactive
            ? { x: mouse.x * 2, y: mouse.y * 1.5 }
            : { x: [0, 30, 0], y: [0, 20, 0] }
        }
        transition={{ type: 'spring', damping: 30, stiffness: 50 }}
      />
      <motion.div
        className="cinematic-orb cinematic-orb-accent absolute rounded-full"
        style={{
          width: `${20 * orbScale}rem`,
          height: `${20 * orbScale}rem`,
          right: `${100 - mouse.x * 0.2}%`,
          bottom: `${100 - mouse.y * 0.15}%`,
        }}
        animate={
          interactive
            ? { x: -mouse.x * 1.5, y: -mouse.y * 2 }
            : { x: [0, -25, 0], y: [0, -15, 0] }
        }
        transition={{ type: 'spring', damping: 30, stiffness: 50 }}
      />
      {intensity === 'hero' && (
        <div className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-primary/40 to-transparent" />
      )}
    </div>
  );
}

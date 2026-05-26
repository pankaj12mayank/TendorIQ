import type { ReactNode } from 'react';

import { cn } from '@/lib/utils';

export function CinematicSection({
  id,
  children,
  className,
  bordered = false,
}: {
  id?: string;
  children: ReactNode;
  className?: string;
  bordered?: boolean;
}) {
  return (
    <section
      id={id}
      className={cn(
        'relative scroll-mt-24 py-20 md:py-28',
        bordered && 'border-t border-white/5',
        className
      )}
    >
      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">{children}</div>
    </section>
  );
}

export function CinematicSectionHeader({
  eyebrow,
  title,
  description,
  align = 'center',
}: {
  eyebrow?: string;
  title: ReactNode;
  description?: string;
  align?: 'center' | 'left';
}) {
  return (
    <div
      className={cn(
        'mb-12 md:mb-16',
        align === 'center' ? 'mx-auto max-w-3xl text-center' : 'max-w-2xl'
      )}
    >
      {eyebrow && <p className="cinematic-eyebrow mb-4">{eyebrow}</p>}
      <h2 className="cinematic-heading">{title}</h2>
      {description && (
        <p className="mt-4 text-base leading-relaxed text-muted-foreground md:text-lg">
          {description}
        </p>
      )}
    </div>
  );
}

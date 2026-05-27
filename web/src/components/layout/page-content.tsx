import type { ReactNode } from 'react';

import { cn } from '@/lib/utils';

export function PageContent({
  children,
  className,
  size = 'default',
}: {
  children: ReactNode;
  className?: string;
  size?: 'default' | 'wide' | 'narrow';
}) {
  return (
    <div
      className={cn(
        'page-content app-page mx-auto w-full animate-fade-in',
        size === 'wide' && 'max-w-[90rem]',
        size === 'narrow' && 'max-w-3xl',
        size === 'default' && 'max-w-7xl',
        className
      )}
    >
      {children}
    </div>
  );
}

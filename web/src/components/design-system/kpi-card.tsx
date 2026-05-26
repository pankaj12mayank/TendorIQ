'use client';

import type { LucideIcon } from 'lucide-react';

import { cn } from '@/lib/utils';

export function KpiCard({
  title,
  value,
  trend,
  trendUp,
  icon: Icon,
  description,
  className,
}: {
  title: string;
  value: string;
  trend?: string;
  trendUp?: boolean;
  icon: LucideIcon;
  description?: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        'glass-panel group relative overflow-hidden p-5 transition-all duration-300 hover:border-primary/30',
        className
      )}
    >
      <div className="pointer-events-none absolute -right-8 -top-8 h-24 w-24 rounded-full bg-primary/5 blur-2xl opacity-0 transition-opacity group-hover:opacity-100" />
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <p className="font-display text-3xl font-semibold tracking-tight tabular-nums">{value}</p>
          {trend && (
            <p className="text-xs text-muted-foreground">
              <span className={cn('font-medium', trendUp ? 'text-success' : 'text-destructive')}>
                {trend}
              </span>{' '}
              vs last period
            </p>
          )}
          {description && <p className="text-xs text-muted-foreground">{description}</p>}
        </div>
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary transition-transform duration-300 group-hover:scale-105">
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  );
}

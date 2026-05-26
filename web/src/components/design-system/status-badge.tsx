'use client';

import { motion } from 'framer-motion';
import type { LucideIcon } from 'lucide-react';

import { statusIcons } from '@/design-system/icons';
import type { StatusType } from '@/design-system/tokens';
import { cn } from '@/lib/utils';

const statusStyles: Record<
  StatusType,
  { className: string; pulse?: boolean }
> = {
  processing: { className: 'bg-info-muted text-info border-info/20', pulse: true },
  retrying: { className: 'bg-warning-muted text-warning-foreground border-warning/30', pulse: true },
  completed: { className: 'bg-success-muted text-success border-success/25' },
  failed: { className: 'bg-destructive/10 text-destructive border-destructive/25' },
  needs_review: { className: 'bg-warning-muted text-warning-foreground border-warning/30' },
  uploaded: { className: 'bg-primary-muted text-primary border-primary/20' },
  archived: { className: 'bg-muted text-muted-foreground border-border' },
  draft: { className: 'bg-muted text-muted-foreground border-border' },
  published: { className: 'bg-success-muted text-success border-success/25' },
};

export function StatusBadge({
  status,
  label,
  className,
  showIcon = true,
}: {
  status: StatusType;
  label?: string;
  className?: string;
  showIcon?: boolean;
}) {
  const Icon = statusIcons[status] as LucideIcon;
  const style = statusStyles[status];
  const text = label ?? status.replace(/_/g, ' ');

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize',
        style.className,
        className
      )}
    >
      {showIcon && (
        <Icon
          className={cn('h-3.5 w-3.5', style.pulse && 'animate-spin')}
          aria-hidden
        />
      )}
      {text}
    </span>
  );
}

export function StatusDot({ status, className }: { status: StatusType; className?: string }) {
  const colors: Record<StatusType, string> = {
    processing: 'bg-info',
    retrying: 'bg-warning',
    completed: 'bg-success',
    failed: 'bg-destructive',
    needs_review: 'bg-warning',
    uploaded: 'bg-primary',
    archived: 'bg-muted-foreground',
    draft: 'bg-muted-foreground',
    published: 'bg-success',
  };

  return (
    <motion.span
      className={cn('relative flex h-2 w-2', className)}
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
    >
      <span className={cn('absolute inline-flex h-full w-full rounded-full opacity-40 animate-ping', colors[status])} />
      <span className={cn('relative inline-flex h-2 w-2 rounded-full', colors[status])} />
    </motion.span>
  );
}

'use client';

import { motion } from 'framer-motion';
import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';

import { cn } from '@/lib/utils';
import { staggerContainer, fadeIn } from '@/design-system/motion';

export type PipelineStep = {
  id: string;
  label: string;
  description?: string;
  status: 'pending' | 'active' | 'completed' | 'failed';
};

export function AiProcessingPipeline({
  title = 'AI Processing',
  steps,
  className,
  animated = true,
}: {
  title?: string;
  steps: PipelineStep[];
  className?: string;
  /** When false, uses static markup (operational dashboard — no motion). */
  animated?: boolean;
}) {
  const ListTag = animated ? motion.ol : 'ol';
  const ItemTag = animated ? motion.li : 'li';
  const listProps = animated
    ? { variants: staggerContainer, initial: 'initial' as const, animate: 'animate' as const }
    : {};

  return (
    <div className={cn('surface-glass p-6', className)}>
      <h3 className="font-display text-lg font-semibold mb-6">{title}</h3>
      <ListTag {...listProps} className="relative space-y-0">
        {steps.map((step, index) => (
          <ItemTag
            key={step.id}
            {...(animated ? { variants: fadeIn } : {})}
            className="relative flex gap-4 pb-8 last:pb-0"
          >
            {index < steps.length - 1 && (
              <span
                className={cn(
                  'absolute left-[15px] top-8 h-[calc(100%-8px)] w-px',
                  step.status === 'completed' ? 'bg-success/50' : 'bg-border'
                )}
              />
            )}
            <StepIndicator status={step.status} animated={animated} />
            <div className="pt-0.5">
              <p className="text-sm font-medium">{step.label}</p>
              {step.description && (
                <p className="text-xs text-muted-foreground mt-0.5">{step.description}</p>
              )}
            </div>
          </ItemTag>
        ))}
      </ListTag>
    </div>
  );
}

function StepIndicator({
  status,
  animated,
}: {
  status: PipelineStep['status'];
  animated: boolean;
}) {
  if (status === 'completed') {
    return (
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-success-muted text-success">
        <CheckCircle2 className="h-4 w-4" />
      </span>
    );
  }
  if (status === 'active') {
    return (
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary ring-2 ring-primary/30">
        <Loader2 className={cn('h-4 w-4', animated && 'animate-spin')} />
      </span>
    );
  }
  if (status === 'failed') {
    return (
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-destructive/15 text-destructive ring-2 ring-destructive/30">
        <AlertCircle className="h-4 w-4" />
      </span>
    );
  }
  return <span className="flex h-8 w-8 shrink-0 rounded-full border-2 border-border bg-muted" />;
}

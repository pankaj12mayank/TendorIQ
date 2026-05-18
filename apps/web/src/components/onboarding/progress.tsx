'use client';

import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ProgressProps {
  currentStep: number;
  totalSteps: number;
}

const steps = [
  { number: 1, label: 'Organization' },
  { number: 2, label: 'Company Profile' },
  { number: 3, label: 'Expertise' },
  { number: 4, label: 'Plan' },
  { number: 5, label: 'Dashboard' },
];

export function OnboardingProgress({ currentStep, totalSteps }: ProgressProps) {
  return (
    <nav aria-label="Progress">
      <ol className="flex items-center justify-between">
        {steps.map((step, index) => {
          const isCompleted = step.number < currentStep;
          const isCurrent = step.number === currentStep;
          const isLast = index === steps.length - 1;

          return (
            <li
              key={step.number}
              className={cn('flex flex-1 items-center', !isLast && 'pr-4')}
            >
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    'flex h-10 w-10 items-center justify-center rounded-full border-2 text-sm font-semibold transition-colors',
                    isCompleted && 'border-primary bg-primary text-primary-foreground',
                    isCurrent && 'border-primary bg-primary text-primary-foreground',
                    !isCompleted && !isCurrent && 'border-muted-foreground/30 bg-background text-muted-foreground'
                  )}
                >
                  {isCompleted ? (
                    <Check className="h-5 w-5" />
                  ) : (
                    step.number
                  )}
                </div>
                <span
                  className={cn(
                    'mt-2 text-xs font-medium',
                    (isCompleted || isCurrent) ? 'text-foreground' : 'text-muted-foreground'
                  )}
                >
                  {step.label}
                </span>
              </div>
              {!isLast && (
                <div
                  className={cn(
                    'mx-2 h-0.5 flex-1 transition-colors',
                    step.number < currentStep ? 'bg-primary' : 'bg-muted-foreground/30'
                  )}
                />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
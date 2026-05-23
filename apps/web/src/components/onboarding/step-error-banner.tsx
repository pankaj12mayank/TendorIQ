'use client';

import { AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useOnboardingApi } from '@/hooks/use-onboarding';

export function OnboardingStepErrorBanner() {
  const { error, failedStep, clearStepError, fetchStatus, loading } = useOnboardingApi();

  if (!error) return null;

  return (
    <div className="mb-6 flex flex-col gap-3 rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
      <div className="flex items-start gap-2">
        <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
        <div>
          {failedStep ? <p className="font-medium">Step {failedStep} failed</p> : null}
          <p>{error}</p>
        </div>
      </div>
      <Button
        type="button"
        variant="outline"
        size="sm"
        className="w-fit"
        disabled={loading}
        onClick={() => {
          clearStepError();
          void fetchStatus();
        }}
      >
        Reload progress from server
      </Button>
    </div>
  );
}

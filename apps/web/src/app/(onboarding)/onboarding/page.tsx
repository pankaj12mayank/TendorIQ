'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useOnboardingStore } from '@/stores/onboarding-store';
import { useOnboardingApi } from '@/hooks/use-onboarding';
import { OnboardingStepErrorBanner } from '@/components/onboarding/step-error-banner';
import { OnboardingWizard } from '@/components/onboarding/wizard';
import { OnboardingProgress } from '@/components/onboarding/progress';
import { LoadingState } from '@/components/ui/loading-state';

export default function OnboardingPage() {
  const router = useRouter();
  const [isInitializing, setIsInitializing] = useState(true);
  const store = useOnboardingStore();
  const { fetchStatus, loading } = useOnboardingApi();

  useEffect(() => {
    async function init() {
      try {
        const status = await fetchStatus();
        if (status.is_completed) {
          router.push('/dashboard');
          return;
        }
      } catch {
        // No existing state, stay on onboarding
      } finally {
        setIsInitializing(false);
      }
    }
    init();
  }, [fetchStatus, router]);

  if (isInitializing) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <LoadingState message="Loading your setup..." />
      </div>
    );
  }

  const currentStep = Math.min(Math.max(store.currentStep, 1), 5);

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <div className="border-b bg-card">
        <div className="mx-auto max-w-5xl px-4 py-6">
          <div className="mb-6 text-center">
            <h1 className="text-2xl font-bold">Welcome to TenderIQ</h1>
            <p className="text-muted-foreground mt-1">Let&apos;s set up your account in a few quick steps</p>
          </div>
          <OnboardingProgress currentStep={currentStep} totalSteps={5} />
        </div>
      </div>
      <div className="flex-1">
        <div className="mx-auto max-w-3xl px-4 py-8">
          <OnboardingStepErrorBanner />
          <OnboardingWizard currentStep={currentStep} />
        </div>
      </div>
    </div>
  );
}
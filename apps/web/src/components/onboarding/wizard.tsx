'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useOnboardingStore } from '@/stores/onboarding-store';
import { useOnboardingApi } from '@/hooks/use-onboarding';
import { Step1Organization } from './steps/step1-organization';
import { Step2Profile } from './steps/step2-profile';
import { Step3Expertise } from './steps/step3-expertise';
import { Step4Plan } from './steps/step4-plan';
import { Step5Dashboard } from './steps/step5-dashboard';

interface WizardProps {
  currentStep: number;
}

export function OnboardingWizard({ currentStep }: WizardProps) {
  const router = useRouter();
  const store = useOnboardingStore();

  switch (currentStep) {
    case 1:
      return <Step1Organization />;
    case 2:
      return <Step2Profile />;
    case 3:
      return <Step3Expertise />;
    case 4:
      return <Step4Plan />;
    case 5:
      return <Step5Dashboard />;
    default:
      return <Step1Organization />;
  }
}
export interface OnboardingStatus {
  completed: boolean;
  step?: string;
}

/** Onboarding UI removed in Lite MVP — always treated as complete. */
export async function fetchOnboardingStatusAuthenticated(
  _accessToken: string
): Promise<OnboardingStatus> {
  return { completed: true };
}

export function shouldCompleteOnboardingFirst(
  _status: OnboardingStatus | null,
  _role?: string
): boolean {
  return false;
}

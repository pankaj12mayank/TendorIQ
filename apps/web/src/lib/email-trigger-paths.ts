/** Canonical tenant email trigger paths (contract with OpenAPI). */
export const EMAIL_TRIGGER_PATHS = {
  uploadReceived: 'upload-received',
  processingCompleted: 'processing-completed',
  processingFailed: 'processing-failed',
  quotaExceeded: 'quota-exceeded',
  subscriptionAlert: 'subscription-alert',
} as const;

export type EmailTriggerPath = (typeof EMAIL_TRIGGER_PATHS)[keyof typeof EMAIL_TRIGGER_PATHS];

export function emailTriggerApiPath(trigger: EmailTriggerPath): string {
  return `/api/v1/email/triggers/${trigger}`;
}

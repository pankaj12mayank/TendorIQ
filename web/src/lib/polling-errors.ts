export class PollingTimeoutError extends Error {
  readonly kind = 'timeout' as const;

  constructor(label: string, maxAttempts: number, intervalMs: number) {
    super(
      `${label} is still processing after ${Math.round((maxAttempts * intervalMs) / 1000)}s. Try Refresh or Retry.`
    );
    this.name = 'PollingTimeoutError';
  }
}

export class PollingCancelledError extends Error {
  readonly kind = 'cancelled' as const;

  constructor(label: string) {
    super(`${label} update was cancelled.`);
    this.name = 'PollingCancelledError';
  }
}

export function formatPollingError(err: unknown, label: string): string {
  if (err instanceof PollingTimeoutError || err instanceof PollingCancelledError) {
    return err.message;
  }
  if (err instanceof Error && err.message.includes('Polling timeout')) {
    return new PollingTimeoutError(label, 30, 3000).message;
  }
  if (err instanceof Error && err.message.includes('OCR polling timeout')) {
    return new PollingTimeoutError('OCR', 60, 5000).message;
  }
  if (err instanceof Error) return err.message;
  return `Failed while waiting for ${label.toLowerCase()}.`;
}

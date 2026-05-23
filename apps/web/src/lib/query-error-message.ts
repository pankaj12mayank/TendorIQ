/** Human-readable message from a React Query error (queries use `throwOnError: false`). */
export function getQueryErrorMessage(error: unknown): string | null {
  if (!error) return null;
  if (error instanceof Error) return error.message;
  return 'Request failed';
}

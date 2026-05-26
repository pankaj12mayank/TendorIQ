/** Clerk env detection — safe in middleware (server) and client bundles. */

const PLACEHOLDER_PATTERN = /placeholder|xxx|your_|changeme|example/i;

export function isClerkPublishableKeyConfigured(): boolean {
  const key = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ?? '';
  if (!key || PLACEHOLDER_PATTERN.test(key)) {
    return false;
  }
  return /^pk_(test|live)_[A-Za-z0-9]+$/.test(key) && key.length > 24;
}

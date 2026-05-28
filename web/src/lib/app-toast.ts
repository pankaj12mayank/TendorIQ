import { toast } from 'sonner';

const DEFAULT_DURATION_MS = 4200;

function normalizeMessage(message: string): string {
  const clean = message.trim().replace(/\s+/g, ' ');
  if (!clean) return 'Something went wrong. Please try again.';
  if (/Failed to construct 'URL'|Invalid URL/i.test(clean)) {
    return 'Could not connect to the server. Please refresh and try again.';
  }
  if (/NetworkError|fetch failed|Cannot reach API|connection/i.test(clean)) {
    return 'Unable to reach the server right now. Please try again in a moment.';
  }
  return clean;
}

export const appToast = {
  success: (message: string, description?: string) =>
    toast.success(normalizeMessage(message), {
      description,
      duration: DEFAULT_DURATION_MS,
    }),
  error: (message: string, description?: string) =>
    toast.error(normalizeMessage(message), {
      description,
      duration: 5500,
    }),
  warning: (message: string, description?: string) =>
    toast.warning(normalizeMessage(message), {
      description,
      duration: 5000,
    }),
  info: (message: string, description?: string) =>
    toast.info(normalizeMessage(message), {
      description,
      duration: DEFAULT_DURATION_MS,
    }),
  loading: (message: string) =>
    toast.loading(normalizeMessage(message), {
      duration: Infinity,
    }),
  dismiss: (id?: string | number) => toast.dismiss(id),
};


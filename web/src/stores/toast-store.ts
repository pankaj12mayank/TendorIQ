/**
 * @deprecated Use `sonner` toast library directly.
 * Import `toast` from 'sonner' instead.
 * Example: `import { toast } from 'sonner'; toast.success('Message');`
 */

import { toast as sonnerToast } from 'sonner';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  description?: string;
  duration?: number;
}

/** @deprecated Use `toast` from 'sonner' directly */
export const toast = {
  success: (title: string, description?: string) => sonnerToast.success(description ? `${title}: ${description}` : title),
  error: (title: string, description?: string) => sonnerToast.error(description ? `${title}: ${description}` : title),
  warning: (title: string, description?: string) => sonnerToast.warning(description ? `${title}: ${description}` : title),
  info: (title: string, description?: string) => sonnerToast.info(description ? `${title}: ${description}` : title),
};
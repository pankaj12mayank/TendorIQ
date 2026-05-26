'use client';

import { cn } from '@/lib/utils';
import { DocumentStatus } from '@/stores/document-store';

interface StatusBadgeProps {
  status: DocumentStatus;
  className?: string;
  showLabel?: boolean;
}

const statusConfig: Record<DocumentStatus, { label: string; className: string; icon: string }> = {
  uploaded: { label: 'Uploaded', className: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300', icon: '↑' },
  processing: { label: 'Processing', className: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300', icon: '↻' },
  retrying: { label: 'Retrying', className: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300', icon: '↻' },
  completed: { label: 'Completed', className: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300', icon: '✓' },
  failed: { label: 'Failed', className: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300', icon: '✗' },
  needs_review: { label: 'Needs Review', className: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300', icon: '!' },
  deleted: { label: 'Deleted', className: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300', icon: '⊘' },
};

export function StatusBadge({ status, className, showLabel = true }: StatusBadgeProps) {
  const config = statusConfig[status] || statusConfig.uploaded;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium',
        config.className,
        className
      )}
    >
      <span className="text-sm">{config.icon}</span>
      {showLabel && config.label}
    </span>
  );
}

export function StatusDot({ status, className }: { status: DocumentStatus; className?: string }) {
  const config = statusConfig[status] || statusConfig.uploaded;
  const colorMap: Record<string, string> = {
    'bg-blue-100 text-blue-800': 'bg-blue-500',
    'bg-yellow-100 text-yellow-800': 'bg-yellow-500',
    'bg-orange-100 text-orange-800': 'bg-orange-500',
    'bg-green-100 text-green-800': 'bg-green-500',
    'bg-red-100 text-red-800': 'bg-red-500',
    'bg-purple-100 text-purple-800': 'bg-purple-500',
    'bg-gray-100 text-gray-800': 'bg-gray-500',
  };

  return (
    <span
      className={cn(
        'inline-block h-2 w-2 rounded-full',
        colorMap[config.className] || 'bg-gray-500',
        className
      )}
    />
  );
}
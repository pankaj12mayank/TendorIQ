'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface NotificationItem {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  time: string;
  read: boolean;
}

interface NotificationPanelProps {
  notifications: NotificationItem[];
  onMarkAllRead?: () => void;
  onNotificationClick?: (id: string) => void;
}

export function NotificationPanel({
  notifications,
  onMarkAllRead,
  onNotificationClick,
}: NotificationPanelProps) {
  const typeStyles = {
    info: 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-300',
    success: 'bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-300',
    warning: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900 dark:text-yellow-300',
    error: 'bg-red-100 text-red-600 dark:bg-red-900 dark:text-red-300',
  };

  return (
    <div className="bg-card rounded-xl border overflow-hidden">
      <div className="p-4 border-b flex items-center justify-between">
        <h3 className="font-semibold">Notifications</h3>
        {onMarkAllRead && (
          <button
            onClick={onMarkAllRead}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            Mark all as read
          </button>
        )}
      </div>
      <div className="divide-y max-h-96 overflow-y-auto">
        {notifications.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">No notifications</div>
        ) : (
          notifications.map((notification) => (
            <div
              key={notification.id}
              onClick={() => onNotificationClick?.(notification.id)}
              className={cn(
                'p-4 hover:bg-muted cursor-pointer transition-colors',
                !notification.read && 'bg-blue-50/50 dark:bg-blue-950/50'
              )}
            >
              <div className="flex items-start gap-3">
                <div className={cn('p-2 rounded-full', typeStyles[notification.type])}>
                  <div className="w-2 h-2 rounded-full bg-current" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium">{notification.title}</p>
                  <p className="text-sm text-muted-foreground mt-1">{notification.message}</p>
                  <p className="text-xs text-muted-foreground/60 mt-2">{notification.time}</p>
                </div>
                {!notification.read && (
                  <div className="w-2 h-2 bg-blue-500 rounded-full" />
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

interface ProcessingIndicatorProps {
  status: 'queued' | 'processing' | 'completed' | 'error';
  progress?: number;
  currentStep?: string;
  steps?: string[];
  message?: string;
}

export function ProcessingIndicator({
  status,
  progress = 0,
  currentStep,
  steps = [],
  message,
}: ProcessingIndicatorProps) {
  const statusConfig = {
    queued: { color: 'bg-muted', label: 'Queued' },
    processing: { color: 'bg-blue-500', label: 'Processing' },
    completed: { color: 'bg-green-500', label: 'Completed' },
    error: { color: 'bg-destructive', label: 'Failed' },
  };

  return (
    <div className="bg-card rounded-xl border p-6">
      <div className="flex items-center gap-4 mb-4">
        {status === 'processing' ? (
          <div className="w-10 h-10 border-4 border-blue-200 border-t-blue-500 rounded-full animate-spin" />
        ) : (
          <div className={cn('w-10 h-10 rounded-full', statusConfig[status].color)} />
        )}
        <div>
          <p className="font-semibold">{statusConfig[status].label}</p>
          {message && <p className="text-sm text-muted-foreground">{message}</p>}
        </div>
      </div>

      {progress > 0 && (
        <div className="mb-4">
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-muted-foreground">Progress</span>
            <span className="font-medium">{progress.toFixed(0)}%</span>
          </div>
          <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {steps.length > 0 && (
        <div className="space-y-2">
          {steps.map((step, idx) => (
            <div
              key={idx}
              className={cn(
                'flex items-center gap-3 text-sm',
                currentStep === step ? 'text-blue-600 font-medium' : 'text-muted-foreground'
              )}
            >
              <div
                className={cn(
                  'w-6 h-6 rounded-full flex items-center justify-center text-xs',
                  currentStep === step ? 'bg-blue-500 text-white' : 'bg-muted text-muted-foreground'
                )}
              >
                {idx + 1}
              </div>
              <span>{step}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default {
  NotificationPanel,
  ProcessingIndicator,
};
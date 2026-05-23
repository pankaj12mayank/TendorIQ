'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { Bell, Check, Loader2, Trash2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useNotifications } from '@/hooks/use-notifications';
import { ROUTES } from '@/lib/routes';
import { cn } from '@/lib/utils';

export default function NotificationsPage() {
  const {
    notifications,
    unreadCount,
    isLoading,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    removeNotification,
  } = useNotifications();

  useEffect(() => {
    void fetchNotifications();
  }, [fetchNotifications]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Bell className="h-6 w-6" />
            Notifications
          </h1>
          <p className="text-sm text-muted-foreground">
            {unreadCount > 0 ? `${unreadCount} unread` : 'All caught up'}
          </p>
        </div>
        <div className="flex gap-2">
          {unreadCount > 0 && (
            <Button variant="outline" size="sm" onClick={() => void markAllAsRead()}>
              <Check className="h-4 w-4 mr-1" />
              Mark all read
            </Button>
          )}
          <Button variant="ghost" size="sm" asChild>
            <Link href={ROUTES.dashboard}>Back to dashboard</Link>
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : notifications.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No notifications yet.
          </CardContent>
        </Card>
      ) : (
        <ul className="space-y-2">
          {notifications.map((n) => (
            <li key={n.id}>
              <Card className={cn(!n.isRead && 'border-primary/30 bg-primary/5')}>
                <CardHeader className="py-3">
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-base font-medium">{n.title}</CardTitle>
                    <div className="flex shrink-0 gap-1">
                      {!n.isRead && (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          aria-label="Mark read"
                          onClick={() => void markAsRead(n.id)}
                        >
                          <Check className="h-4 w-4" />
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-destructive"
                        aria-label="Delete"
                        onClick={() => void removeNotification(n.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-0 text-sm text-muted-foreground">
                  <p>{n.message}</p>
                  {n.actionUrl && (
                    <Link href={n.actionUrl} className="mt-2 inline-block text-primary hover:underline">
                      {n.actionLabel ?? 'View'}
                    </Link>
                  )}
                </CardContent>
              </Card>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

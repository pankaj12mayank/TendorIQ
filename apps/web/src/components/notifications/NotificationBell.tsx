'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useNotifications } from '@/hooks/use-notifications';
import { ROUTES } from '@/lib/routes';
import type { Notification } from './store';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { 
  Bell, 
  Check, 
  AlertCircle, 
  Info, 
  AlertTriangle,
  CheckCircle2 
} from 'lucide-react';
import { cn } from '@/lib/utils';

const ICONS = {
  info: Info,
  success: CheckCircle2,
  warning: AlertTriangle,
  error: AlertCircle,
};

export function NotificationBell() {
  const { notifications, unreadCount, markAsRead, markAllAsRead, fetchNotifications } =
    useNotifications();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    void fetchNotifications();
  }, [fetchNotifications]);

  const recentNotifications = notifications.slice(0, 5);

  const getTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m`;
    if (hours < 24) return `${hours}h`;
    return '1d+';
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="w-5 h-5" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-75" />
              <span className="relative inline-flex h-4 w-4 rounded-full bg-red-500 text-[10px] text-white items-center justify-center">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            </span>
          )}
        </Button>
      </PopoverTrigger>
      
      <PopoverContent className="w-80 p-0" align="end">
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold">Notifications</h3>
            {unreadCount > 0 && (
              <Badge className="bg-red-100 text-red-800 text-xs">
                {unreadCount}
              </Badge>
            )}
          </div>
          {unreadCount > 0 && (
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={markAllAsRead}
              className="text-xs"
            >
              <Check className="w-3 h-3 mr-1" />
              Mark all read
            </Button>
          )}
        </div>

        <div className="max-h-96 overflow-y-auto">
          {recentNotifications.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              <Bell className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No notifications</p>
            </div>
          ) : (
            <div className="divide-y">
              {recentNotifications.map((notification) => {
                const Icon = ICONS[notification.type];
                
                return (
                  <div
                    key={notification.id}
                    className={cn(
                      'p-3 hover:bg-muted/50 cursor-pointer transition-colors',
                      !notification.isRead && 'bg-blue-50/50'
                    )}
                    onClick={() => markAsRead(notification.id)}
                  >
                    <div className="flex items-start gap-3">
                      <div className={cn(
                        'p-1.5 rounded-full flex-shrink-0',
                        notification.type === 'info' && 'bg-blue-100 text-blue-600',
                        notification.type === 'success' && 'bg-green-100 text-green-600',
                        notification.type === 'warning' && 'bg-yellow-100 text-yellow-600',
                        notification.type === 'error' && 'bg-red-100 text-red-600'
                      )}>
                        <Icon className="w-3 h-3" />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2">
                          <p className={cn(
                            'text-sm truncate',
                            !notification.isRead && 'font-medium'
                          )}>
                            {notification.title}
                          </p>
                          <span className="text-xs text-muted-foreground flex-shrink-0">
                            {getTimeAgo(notification.createdAt)}
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground line-clamp-2 mt-0.5">
                          {notification.message}
                        </p>
                      </div>
                    </div>
                    
                    {!notification.isRead && (
                      <div className="absolute left-2 top-1/2 -translate-y-1/2 w-1.5 h-1.5 bg-blue-500 rounded-full" />
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="p-2 border-t">
          <Button variant="outline" className="w-full text-xs" asChild onClick={() => setOpen(false)}>
            <Link href={ROUTES.notifications}>View all notifications</Link>
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
}

export default NotificationBell;
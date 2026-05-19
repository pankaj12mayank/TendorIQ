'use client';

import React, { useState } from 'react';
import { useNotificationStore, Notification } from './store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Bell, 
  Check, 
  CheckCheck, 
  X, 
  AlertCircle, 
  Info, 
  AlertTriangle, 
  CheckCircle2,
  ExternalLink,
  Trash2
} from 'lucide-react';
import { cn } from '@/lib/utils';

const ICONS = {
  info: Info,
  success: CheckCircle2,
  warning: AlertTriangle,
  error: AlertCircle,
};

const COLORS = {
  info: 'bg-blue-100 text-blue-600 border-blue-200',
  success: 'bg-green-100 text-green-600 border-green-200',
  warning: 'bg-yellow-100 text-yellow-600 border-yellow-200',
  error: 'bg-red-100 text-red-600 border-red-200',
};

interface NotificationItemProps {
  notification: Notification;
  onMarkRead: (id: string) => void;
  onRemove: (id: string) => void;
}

function NotificationItem({ notification, onMarkRead, onRemove }: NotificationItemProps) {
  const Icon = ICONS[notification.type];
  const colorClass = COLORS[notification.type];
  
  const timeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  return (
    <div className={cn(
      'p-4 border rounded-lg transition-all',
      !notification.isRead && 'bg-blue-50/50 border-blue-200',
      notification.isRead && 'bg-card'
    )}>
      <div className="flex items-start gap-3">
        <div className={cn('p-2 rounded-lg flex-shrink-0', colorClass)}>
          <Icon className="w-4 h-4" />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className={cn(
                'font-medium text-sm',
                !notification.isRead && 'font-semibold'
              )}>
                {notification.title}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                {notification.message}
              </p>
            </div>
            
            <button
              onClick={() => onRemove(notification.id)}
              className="text-muted-foreground hover:text-foreground p-1"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          
          <div className="flex items-center gap-3 mt-3">
            <span className="text-xs text-muted-foreground">
              {timeAgo(notification.createdAt)}
            </span>
            
            {!notification.isRead && (
              <button
                onClick={() => onMarkRead(notification.id)}
                className="text-xs text-blue-600 hover:underline"
              >
                Mark as read
              </button>
            )}
            
            {notification.actionUrl && (
              <a
                href={notification.actionUrl}
                className="text-xs text-blue-600 hover:underline flex items-center gap-1"
              >
                {notification.actionLabel || 'View'} <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

interface NotificationCenterProps {
  className?: string;
  maxHeight?: string;
}

export function NotificationCenter({ className, maxHeight = '600px' }: NotificationCenterProps) {
  const { 
    notifications, 
    unreadCount, 
    markAsRead, 
    markAllAsRead, 
    removeNotification,
    clearAll,
    isLoading 
  } = useNotificationStore();
  
  const [filter, setFilter] = useState<'all' | 'unread'>('all');
  
  const filteredNotifications = filter === 'unread'
    ? notifications.filter(n => !n.isRead)
    : notifications;

  return (
    <Card className={cn(className)}>
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <div className="flex items-center gap-3">
          <CardTitle className="text-lg">Notifications</CardTitle>
          {unreadCount > 0 && (
            <Badge className="bg-blue-100 text-blue-800">
              {unreadCount} unread
            </Badge>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          <Button 
            variant="ghost" 
            size="sm"
            onClick={markAllAsRead}
            disabled={unreadCount === 0}
          >
            <CheckCheck className="w-4 h-4 mr-1" />
            Mark all read
          </Button>
          <Button 
            variant="ghost" 
            size="sm"
            onClick={clearAll}
            disabled={notifications.length === 0}
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-3">
        <div className="flex items-center gap-2 pb-2">
          <Button
            variant={filter === 'all' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter('all')}
          >
            All
          </Button>
          <Button
            variant={filter === 'unread' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter('unread')}
          >
            Unread
          </Button>
        </div>
        
        <div 
          className="space-y-2 overflow-y-auto"
          style={{ maxHeight }}
        >
          {filteredNotifications.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Bell className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No notifications</p>
            </div>
          ) : (
            filteredNotifications.map((notification) => (
              <NotificationItem
                key={notification.id}
                notification={notification}
                onMarkRead={markAsRead}
                onRemove={removeNotification}
              />
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default NotificationCenter;
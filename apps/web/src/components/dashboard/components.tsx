'use client';

import React, { useState, useCallback } from 'react';
import { Upload, X, CheckCircle, AlertCircle, Loader2, FileText, Image, File } from 'lucide-react';
import { cn } from '@/lib/utils';

interface UploadFile {
  id: string;
  file: File;
  name: string;
  size: number;
  progress: number;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
  result?: unknown;
}

interface UploadTrackerProps {
  onUploadComplete?: (results: unknown[]) => void;
  maxFiles?: number;
  acceptedTypes?: string[];
  maxSizeMB?: number;
}

export function UploadTracker({
  onUploadComplete,
  maxFiles = 10,
  acceptedTypes = ['.pdf', '.doc', '.docx', '.jpg', '.png'],
  maxSizeMB = 10,
}: UploadTrackerProps) {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    if (['pdf'].includes(ext || '')) return <FileText className="w-5 h-5 text-red-500" />;
    if (['jpg', 'jpeg', 'png', 'gif'].includes(ext || '')) return <Image className="w-5 h-5 text-blue-500" />;
    return <File className="w-5 h-5 text-muted-foreground" />;
  };

  const simulateUpload = (fileId: string) => {
    setFiles((prev) =>
      prev.map((f) => (f.id === fileId ? { ...f, status: 'uploading' as const } : f))
    );

    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 15;
      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
        setFiles((prev) =>
          prev.map((f) =>
            f.id === fileId ? { ...f, progress: 100, status: 'processing' as const } : f
          )
        );
        setTimeout(() => {
          setFiles((prev) =>
            prev.map((f) =>
              f.id === fileId ? { ...f, status: 'completed' as const } : f
            )
          );
        }, 500);
      } else {
        setFiles((prev) =>
          prev.map((f) => (f.id === fileId ? { ...f, progress } : f))
        );
      }
    }, 200);
  };

  const handleFiles = useCallback((newFiles: FileList) => {
    const validFiles = Array.from(newFiles).slice(0, maxFiles - files.length);

    const uploadFiles: UploadFile[] = validFiles.map((file) => ({
      id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      file,
      name: file.name,
      size: file.size,
      progress: 0,
      status: 'pending' as const,
    }));

    setFiles((prev) => [...prev, ...uploadFiles]);

    uploadFiles.forEach((uploadFile) => {
      simulateUpload(uploadFile.id);
    });
  }, [files.length, maxFiles]);

  const removeFile = (fileId: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId));
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files.length) {
      handleFiles(e.dataTransfer.files);
    }
  }, [handleFiles]);

  return (
    <div className="space-y-4">
      <div
        onDrop={handleDrop}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={(e) => { e.preventDefault(); setIsDragging(false); }}
        className={cn(
          'border-2 border-dashed rounded-xl p-8 text-center transition-colors',
          isDragging ? 'border-blue-500 bg-blue-50' : 'border-border hover:border-muted-foreground/50'
        )}
      >
        <Upload className={cn('w-12 h-12 mx-auto mb-4', isDragging ? 'text-blue-600' : 'text-muted-foreground')} />
        <p className="text-muted-foreground mb-2">
          Drag and drop files here, or
          <label className="text-blue-600 hover:text-blue-700 cursor-pointer mx-1">
            browse
            <input
              type="file"
              multiple
              accept={acceptedTypes.join(',')}
              className="hidden"
              onChange={(e) => e.target.files && handleFiles(e.target.files)}
            />
          </label>
        </p>
        <p className="text-sm text-muted-foreground/60">
          {acceptedTypes.join(', ')} up to {maxSizeMB}MB
        </p>
      </div>

      <div className="space-y-2">
        {files.map((file) => (
          <div
            key={file.id}
            className="flex items-center gap-4 p-4 bg-card rounded-lg border"
          >
            {getFileIcon(file.name)}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <p className="font-medium truncate">{file.name}</p>
                <span className="text-sm text-muted-foreground">{formatFileSize(file.size)}</span>
              </div>
              <div className="mt-2 flex items-center gap-3">
                <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className={cn(
                      'h-full rounded-full transition-all',
                      file.status === 'error' ? 'bg-destructive' : 'bg-blue-500'
                    )}
                    style={{ width: `${file.progress}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-muted-foreground">
                  {file.progress.toFixed(0)}%
                </span>
              </div>
              <div className="mt-1">
                {file.status === 'pending' && <span className="text-xs text-muted-foreground">Waiting...</span>}
                {file.status === 'uploading' && <span className="text-xs text-blue-600">Uploading...</span>}
                {file.status === 'processing' && (
                  <span className="text-xs text-yellow-600 flex items-center gap-1">
                    <Loader2 className="w-3 h-3 animate-spin" /> Processing...
                  </span>
                )}
                {file.status === 'completed' && (
                  <span className="text-xs text-green-600 flex items-center gap-1">
                    <CheckCircle className="w-3 h-3" /> Completed
                  </span>
                )}
                {file.status === 'error' && (
                  <span className="text-xs text-destructive flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" /> {file.error || 'Failed'}
                  </span>
                )}
              </div>
            </div>
            <button
              onClick={() => removeFile(file.id)}
              className="p-2 text-muted-foreground hover:text-destructive rounded hover:bg-muted"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

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
  UploadTracker,
  NotificationPanel,
  ProcessingIndicator,
};
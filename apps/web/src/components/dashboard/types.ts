export interface ChartDataPoint {
  label: string;
  value: number;
}

export interface DonutChartDataPoint extends ChartDataPoint {
  color: string;
}

export interface ActivityItem {
  id: string;
  type: 'upload' | 'process' | 'complete' | 'error';
  title: string;
  description?: string;
  time: string;
}

export interface UploadFileData {
  id: string;
  file: File;
  name: string;
  size: number;
  progress: number;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
  result?: unknown;
}

export interface NotificationData {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  time: string;
  read: boolean;
}

export interface DashboardStats {
  title: string;
  value: string;
  trend: string;
  trendDirection: 'up' | 'down' | 'neutral';
}

export interface ProcessingStep {
  label: string;
  status: 'pending' | 'in-progress' | 'completed' | 'error';
}
import { ActivityItem, NotificationData, ChartDataPoint } from './types';

export const DEFAULT_LINE_CHART_DATA: ChartDataPoint[] = [
  { label: 'Jan', value: 30 },
  { label: 'Feb', value: 45 },
  { label: 'Mar', value: 60 },
  { label: 'Apr', value: 55 },
  { label: 'May', value: 70 },
  { label: 'Jun', value: 85 },
];

export const DEFAULT_BAR_CHART_DATA = [
  { label: 'Jan', value: 40, color: '#3b82f6' },
  { label: 'Feb', value: 60, color: '#3b82f6' },
  { label: 'Mar', value: 45, color: '#3b82f6' },
  { label: 'Apr', value: 80, color: '#3b82f6' },
  { label: 'May', value: 65, color: '#3b82f6' },
];

export const DEFAULT_DONUT_CHART_DATA = [
  { label: 'Completed', value: 65, color: '#22c55e' },
  { label: 'In Progress', value: 25, color: '#3b82f6' },
  { label: 'Pending', value: 10, color: '#f59e0b' },
];

export const SAMPLE_ACTIVITIES: ActivityItem[] = [
  {
    id: '1',
    type: 'complete',
    title: 'Document processed successfully',
    description: 'Annual Report 2024.pdf was processed',
    time: '2 minutes ago',
  },
  {
    id: '2',
    type: 'process',
    title: 'Processing tender submission',
    description: 'RFP-2024-001 is being analyzed',
    time: '5 minutes ago',
  },
  {
    id: '3',
    type: 'upload',
    title: 'New document uploaded',
    description: 'Budget Proposal Q4.pdf uploaded',
    time: '15 minutes ago',
  },
];

export const SAMPLE_NOTIFICATIONS: NotificationData[] = [
  {
    id: '1',
    type: 'success',
    title: 'Tender Submitted',
    message: 'Your bid for Project Alpha has been submitted successfully.',
    time: '2 hours ago',
    read: false,
  },
  {
    id: '2',
    type: 'info',
    title: 'New Tender Available',
    message: 'A new tender matching your criteria is now available.',
    time: '5 hours ago',
    read: true,
  },
  {
    id: '3',
    type: 'warning',
    title: 'Deadline Approaching',
    message: 'RFP-2024-001 deadline is in 2 days.',
    time: '1 day ago',
    read: false,
  },
  {
    id: '4',
    type: 'error',
    title: 'Upload Failed',
    message: 'Document upload failed. Please try again.',
    time: '2 days ago',
    read: true,
  },
];

export const PROCESSING_STEPS = [
  'Uploading document',
  'Extracting text',
  'Analyzing content',
  'Generating report',
];

export const CHART_COLORS = {
  primary: '#3b82f6',
  success: '#22c55e',
  warning: '#f59e0b',
  error: '#ef4444',
  gray: '#6b7280',
};
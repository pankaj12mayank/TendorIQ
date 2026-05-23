import type { LucideIcon } from 'lucide-react';
import {
  LayoutDashboard,
  Upload,
  ShieldAlert,
  CreditCard,
  Download,
  Settings,
  Users,
  Shield,
  ListTodo,
  Sparkles,
  Bell,
  FileText,
  Briefcase,
  BarChart3,
  Building2,
  ClipboardCheck,
  FileSearch,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  RefreshCw,
  Archive,
  Inbox,
} from 'lucide-react';

import type { AppRole } from './tokens';
import type { StatusType } from './tokens';

export const moduleIcons: Record<string, LucideIcon> = {
  dashboard: LayoutDashboard,
  tenders: FileText,
  bids: Briefcase,
  upload: Upload,
  risks: ShieldAlert,
  billing: CreditCard,
  exports: Download,
  settings: Settings,
  users: Users,
  admin: Shield,
  queue: ListTodo,
  ai: Sparkles,
  notifications: Bell,
  analytics: BarChart3,
  organizations: Building2,
  compliance: ClipboardCheck,
  extraction: FileSearch,
};

export const statusIcons: Record<StatusType, LucideIcon> = {
  processing: Loader2,
  retrying: RefreshCw,
  completed: CheckCircle2,
  failed: AlertTriangle,
  needs_review: FileSearch,
  uploaded: Upload,
  archived: Archive,
  draft: Inbox,
  published: CheckCircle2,
};

export const roleNavGroups: Record<
  AppRole,
  { label: string; items: { name: string; href: string; icon: LucideIcon }[] }[]
> = {
  super_admin: [
    {
      label: 'Platform',
      items: [
        { name: 'Admin Console', href: '/dashboard/admin?module=users', icon: Shield },
        { name: 'Analytics', href: '/dashboard/admin?module=analytics', icon: BarChart3 },
        { name: 'Queue', href: '/dashboard/admin?module=queue', icon: ListTodo },
      ],
    },
  ],
  tenant_admin: [
    {
      label: 'Workspace',
      items: [
        { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
        { name: 'Tenders', href: '/dashboard/tenders', icon: FileText },
        { name: 'Bids', href: '/dashboard/bids', icon: Briefcase },
        { name: 'Upload', href: '/dashboard/upload', icon: Upload },
      ],
    },
    {
      label: 'Organization',
      items: [
        { name: 'Team', href: '/dashboard/organizations', icon: Users },
        { name: 'Billing', href: '/dashboard/billing', icon: CreditCard },
        { name: 'Usage', href: '/dashboard/usage', icon: BarChart3 },
      ],
    },
  ],
  manager: [
    {
      label: 'Management',
      items: [
        { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
        { name: 'Tenders', href: '/dashboard/tenders', icon: FileText },
        { name: 'Bids', href: '/dashboard/bids', icon: Briefcase },
        { name: 'Upload', href: '/dashboard/upload', icon: Upload },
        { name: 'Review', href: '/dashboard/tenders/review', icon: ClipboardCheck },
      ],
    },
    {
      label: 'Organization',
      items: [
        { name: 'Team', href: '/dashboard/organizations', icon: Users },
        { name: 'Billing', href: '/dashboard/billing', icon: CreditCard },
        { name: 'Usage', href: '/dashboard/usage', icon: BarChart3 },
        { name: 'Settings', href: '/dashboard/settings', icon: Settings },
      ],
    },
  ],
  analyst: [
    {
      label: 'Analysis',
      items: [
        { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
        { name: 'Tenders', href: '/dashboard/tenders', icon: FileText },
        { name: 'Bids', href: '/dashboard/bids', icon: Briefcase },
        { name: 'Upload', href: '/dashboard/upload', icon: Upload },
        { name: 'Analytics', href: '/dashboard/analytics', icon: BarChart3 },
      ],
    },
    {
      label: 'Reference',
      items: [
        { name: 'Documents', href: '/dashboard/documents', icon: FileText },
        { name: 'Notifications', href: '/dashboard/notifications', icon: Bell },
      ],
    },
  ],
  member: [
    {
      label: 'Work',
      items: [
        { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
        { name: 'Tenders', href: '/dashboard/tenders', icon: FileText },
        { name: 'Bids', href: '/dashboard/bids', icon: Briefcase },
        { name: 'Upload', href: '/dashboard/upload', icon: Upload },
      ],
    },
    {
      label: 'Organization',
      items: [
        { name: 'Usage', href: '/dashboard/usage', icon: BarChart3 },
      ],
    },
  ],
  viewer: [
    {
      label: 'View',
      items: [
        { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
        { name: 'Tenders', href: '/dashboard/tenders', icon: FileText },
        { name: 'Bids', href: '/dashboard/bids', icon: Briefcase },
        { name: 'Documents', href: '/dashboard/documents', icon: FileText },
      ],
    },
  ],
  user: [
    {
      label: 'Work',
      items: [
        { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
        { name: 'Tenders', href: '/dashboard/tenders', icon: FileText },
        { name: 'Bids', href: '/dashboard/bids', icon: Briefcase },
        { name: 'Upload', href: '/dashboard/upload', icon: Upload },
        { name: 'Usage', href: '/dashboard/usage', icon: BarChart3 },
      ],
    },
  ],
};

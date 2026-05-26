import type { LucideIcon } from 'lucide-react';
import {
  LayoutDashboard,
  Upload,
  FileSearch,
  FileText,
  Settings,
  Shield,
} from 'lucide-react';

import type { AppRole } from './tokens';

import type { StatusType } from './tokens';
import { Loader2, RefreshCw, CheckCircle2, AlertTriangle, Upload, Archive, Inbox } from 'lucide-react';

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

export const moduleIcons: Record<string, LucideIcon> = {
  dashboard: LayoutDashboard,
  upload: Upload,
  analysis: FileSearch,
  proposal: FileText,
  settings: Settings,
  admin: Shield,
};

export const roleNavGroups: Record<
  AppRole,
  { label: string; items: { name: string; href: string; icon: LucideIcon }[] }[]
> = {
  super_admin: [
    {
      label: 'Platform',
      items: [{ name: 'Admin', href: '/dashboard/admin', icon: Shield }],
    },
  ],
  tenant_admin: [
    {
      label: 'Workspace',
      items: [
        { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
        { name: 'Upload', href: '/dashboard/upload', icon: Upload },
        { name: 'Analysis', href: '/dashboard/analysis', icon: FileSearch },
        { name: 'Proposal', href: '/dashboard/proposal', icon: FileText },
        { name: 'Settings', href: '/dashboard/settings', icon: Settings },
      ],
    },
  ],
  manager: [
    {
      label: 'Workspace',
      items: [
        { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
        { name: 'Upload', href: '/dashboard/upload', icon: Upload },
        { name: 'Analysis', href: '/dashboard/analysis', icon: FileSearch },
        { name: 'Proposal', href: '/dashboard/proposal', icon: FileText },
        { name: 'Settings', href: '/dashboard/settings', icon: Settings },
      ],
    },
  ],
  analyst: [
    {
      label: 'Workspace',
      items: [
        { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
        { name: 'Upload', href: '/dashboard/upload', icon: Upload },
        { name: 'Analysis', href: '/dashboard/analysis', icon: FileSearch },
        { name: 'Proposal', href: '/dashboard/proposal', icon: FileText },
      ],
    },
  ],
  member: [
    {
      label: 'Workspace',
      items: [
        { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
        { name: 'Upload', href: '/dashboard/upload', icon: Upload },
        { name: 'Analysis', href: '/dashboard/analysis', icon: FileSearch },
      ],
    },
  ],
  viewer: [
    {
      label: 'Workspace',
      items: [
        { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
        { name: 'Analysis', href: '/dashboard/analysis', icon: FileSearch },
      ],
    },
  ],
  user: [
    {
      label: 'Workspace',
      items: [
        { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
        { name: 'Upload', href: '/dashboard/upload', icon: Upload },
        { name: 'Analysis', href: '/dashboard/analysis', icon: FileSearch },
        { name: 'Proposal', href: '/dashboard/proposal', icon: FileText },
        { name: 'Settings', href: '/dashboard/settings', icon: Settings },
      ],
    },
  ],
};

import type { LucideIcon } from 'lucide-react';
import {
  AlertTriangle,
  Archive,
  CheckCircle2,
  FileSearch,
  FileText,
  Inbox,
  LayoutDashboard,
  Loader2,
  RefreshCw,
  Settings,
  Shield,
  Upload,
} from 'lucide-react';

import type { AppRole, StatusType } from './tokens';

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

const workspaceNavItems = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Upload', href: '/dashboard/upload', icon: Upload },
  { name: 'Analysis', href: '/dashboard/analysis', icon: FileSearch },
  { name: 'Proposal', href: '/dashboard/proposal', icon: FileText },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
] as const;

const workspaceNavGroup = {
  label: 'Workspace',
  items: [...workspaceNavItems],
};

const platformAdminGroup = {
  label: 'Platform',
  items: [{ name: 'Admin', href: '/dashboard/admin', icon: Shield }],
};

export const roleNavGroups: Record<
  AppRole,
  { label: string; items: { name: string; href: string; icon: LucideIcon }[] }[]
> = {
  super_admin: [workspaceNavGroup, platformAdminGroup],
  tenant_admin: [workspaceNavGroup],
  owner: [workspaceNavGroup],
  admin: [workspaceNavGroup],
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
  user: [workspaceNavGroup],
};

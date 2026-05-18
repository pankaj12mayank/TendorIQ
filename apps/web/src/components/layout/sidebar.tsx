'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  FileText,
  Users,
  Settings,
  Briefcase,
  BarChart3,
  Upload,
} from 'lucide-react';
import { useTenantStore } from '@/stores/tenant-store';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Tenders', href: '/dashboard/tenders', icon: FileText },
  { name: 'Bids', href: '/dashboard/bids', icon: Briefcase },
  { name: 'Upload', href: '/dashboard/upload', icon: Upload },
  { name: 'Organizations', href: '/dashboard/organizations', icon: Users },
  { name: 'Analytics', href: '/dashboard/analytics', icon: BarChart3 },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const currentOrganization = useTenantStore((s) => s.currentOrganization);

  const planName = currentOrganization?.role === 'owner' ? 'Pro Plan' : 'Standard';
  const memberCount = '5 team members';

  return (
    <aside className="hidden w-64 flex-col border-r bg-card lg:flex">
      <div className="flex h-16 items-center border-b px-6">
        <Link href="/dashboard" className="text-xl font-bold">
          TenderIQ
        </Link>
      </div>
      <nav className="flex-1 space-y-1 p-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>
      <div className="border-t p-4">
        <div className="rounded-lg bg-muted p-3">
          <p className="text-sm font-medium">{planName}</p>
          <p className="text-xs text-muted-foreground">{memberCount}</p>
        </div>
      </div>
    </aside>
  );
}
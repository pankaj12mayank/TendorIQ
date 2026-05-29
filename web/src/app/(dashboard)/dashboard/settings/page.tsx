'use client';

import { useRouter, useSearchParams } from 'next/navigation';

import { PageHeader } from '@/components/design-system/page-header';
import { BillingPanel } from '@/components/settings/billing-panel';
import { ProfilePanel } from '@/components/settings/profile-panel';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ROUTES, SETTINGS_TABS, type SettingsTab } from '@/lib/routes';

function parseTab(raw: string | null): SettingsTab {
  if (raw === 'billing') return 'billing';
  if (raw === 'account' || raw === 'profile') return 'account';
  if (raw && SETTINGS_TABS.includes(raw as SettingsTab)) {
    return raw as SettingsTab;
  }
  return 'account';
}

export default function SettingsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const tab = parseTab(searchParams.get('tab'));

  const setTab = (next: SettingsTab) => {
    router.replace(`${ROUTES.settings}?tab=${next}`, { scroll: false });
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title="Settings"
        description="Manage your account password and subscription."
      />

      <Tabs value={tab} onValueChange={(v) => setTab(parseTab(v))} className="w-full space-y-6">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="account">Account</TabsTrigger>
          <TabsTrigger value="billing">Billing</TabsTrigger>
        </TabsList>
        <TabsContent value="account" className="mt-0 focus-visible:outline-none">
          <ProfilePanel />
        </TabsContent>
        <TabsContent value="billing" className="mt-0 focus-visible:outline-none">
          <BillingPanel />
        </TabsContent>
      </Tabs>
    </div>
  );
}

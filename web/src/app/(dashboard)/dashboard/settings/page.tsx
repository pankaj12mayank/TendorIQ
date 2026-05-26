'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

import { AiPanel } from '@/components/settings/ai-panel';
import { BillingPanel } from '@/components/settings/billing-panel';
import { ProfilePanel } from '@/components/settings/profile-panel';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ROUTES, SETTINGS_TABS, type SettingsTab } from '@/lib/routes';

function parseTab(raw: string | null): SettingsTab {
  if (raw && SETTINGS_TABS.includes(raw as SettingsTab)) {
    return raw as SettingsTab;
  }
  return 'profile';
}

export default function SettingsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const tab = parseTab(searchParams.get('tab'));

  const setTab = (next: SettingsTab) => {
    router.replace(`${ROUTES.settings}?tab=${next}`, { scroll: false });
  };

  useEffect(() => {
    if (searchParams.get('tab') === 'company') {
      router.replace(`${ROUTES.settings}?tab=profile`, { scroll: false });
      requestAnimationFrame(() => {
        document.getElementById('company')?.scrollIntoView({ behavior: 'smooth' });
      });
    }
  }, [searchParams, router]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">Profile, company, AI defaults, and billing in one place.</p>
      </div>

      <Tabs value={tab} onValueChange={(v) => setTab(parseTab(v))}>
        <TabsList>
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="ai">AI</TabsTrigger>
          <TabsTrigger value="billing">Billing</TabsTrigger>
        </TabsList>
        <TabsContent value="profile" className="mt-6">
          <ProfilePanel />
        </TabsContent>
        <TabsContent value="ai" className="mt-6">
          <AiPanel />
        </TabsContent>
        <TabsContent value="billing" className="mt-6">
          <BillingPanel />
        </TabsContent>
      </Tabs>
    </div>
  );
}

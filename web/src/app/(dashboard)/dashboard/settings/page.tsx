'use client';

import { useState } from 'react';
import { User, Bot } from 'lucide-react';

import { ProfilePanel } from '@/components/settings/profile-panel';
import { AiPanel } from '@/components/settings/ai-panel';
import { Button } from '@/components/ui/button';

const tabs = [
  { id: 'account', label: 'Account', icon: User },
  { id: 'ai', label: 'AI Settings', icon: Bot },
] as const;

type Tab = (typeof tabs)[number]['id'];

export default function SettingsPage() {
  const [tab, setTab] = useState<Tab>('account');

  return (
    <div className="w-full">
      <div className="flex flex-wrap gap-2 rounded-xl border border-border/60 bg-muted/20 p-2" role="tablist">
        {tabs.map((t) => (
          <Button
            key={t.id}
            variant="ghost"
            size="sm"
            className={
              tab === t.id
                ? 'rounded-lg bg-background text-foreground shadow-sm hover:bg-background'
                : 'rounded-lg text-muted-foreground'
            }
            onClick={() => setTab(t.id)}
            role="tab"
            aria-selected={tab === t.id}
          >
            <t.icon className="mr-2 h-4 w-4" />
            {t.label}
          </Button>
        ))}
      </div>

      <div className="mt-6">
        {tab === 'account' && <ProfilePanel />}
        {tab === 'ai' && <AiPanel />}
      </div>
    </div>
  );
}

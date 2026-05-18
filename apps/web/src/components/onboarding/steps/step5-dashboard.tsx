'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { useOnboardingApi, Step5Data } from '@/hooks/use-onboarding';
import { useOnboardingStore } from '@/stores/onboarding-store';
import { AlertCircle, LayoutDashboard, Loader2, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';

const TIMEZONES = [
  'UTC',
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'Europe/London',
  'Europe/Paris',
  'Europe/Berlin',
  'Asia/Dubai',
  'Asia/Kolkata',
  'Asia/Singapore',
  'Asia/Tokyo',
  'Australia/Sydney',
];

const CURRENCIES = ['USD', 'EUR', 'GBP', 'INR', 'AED', 'AUD', 'CAD'];

const LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'es', name: 'Spanish' },
  { code: 'fr', name: 'French' },
  { code: 'de', name: 'German' },
  { code: 'ar', name: 'Arabic' },
  { code: 'zh', name: 'Chinese' },
];

const EMAIL_DIGESTS = [
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'never', label: 'Never' },
];

const DASHBOARD_WIDGETS = [
  { id: 'stats_overview', name: 'Stats Overview', description: 'Key metrics at a glance' },
  { id: 'recent_tenders', name: 'Recent Tenders', description: 'Latest tender activities' },
  { id: 'pending_bids', name: 'Pending Bids', description: 'Bids awaiting action' },
  { id: 'upcoming_deadlines', name: 'Upcoming Deadlines', description: 'Important upcoming dates' },
  { id: 'quick_actions', name: 'Quick Actions', description: 'Common tasks shortcuts' },
];

export function Step5Dashboard() {
  const router = useRouter();
  const store = useOnboardingStore();
  const { submitStep5, loading, error } = useOnboardingApi();

  const [form, setForm] = useState<Step5Data>({
    notifications_enabled: true,
    email_digest: (store.step5Data.email_digest as string) || 'weekly',
    timezone: (store.step5Data.timezone as string) || Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
    currency: (store.step5Data.currency as string) || 'USD',
    language: (store.step5Data.language as string) || 'en',
  });

  const [selectedWidgets, setSelectedWidgets] = useState<string[]>(
    (store.step5Data.widgets as string[] || DASHBOARD_WIDGETS.map((w) => w.id))
  );

  const toggleWidget = (id: string) => {
    setSelectedWidgets((prev) =>
      prev.includes(id) ? prev.filter((w) => w !== id) : [...prev, id]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const data = {
        ...form,
        widgets: DASHBOARD_WIDGETS.map((w, i) => ({
          id: w.id,
          type: w.id,
          enabled: selectedWidgets.includes(w.id),
          position: i,
        })),
      };
      const res = await submitStep5(data);
      if (res.success) {
        router.push('/dashboard');
      }
    } catch {
      // Error handled by hook
    }
  };

  const handleBack = () => {
    store.setCurrentStep(4);
    router.push('/onboarding');
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center gap-2">
          <LayoutDashboard className="h-6 w-6 text-primary" />
          <CardTitle>Dashboard Setup</CardTitle>
        </div>
        <CardDescription>
          Customize your dashboard experience and notification preferences.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="flex items-center gap-2 rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
              <AlertCircle className="h-4 w-4" />
              {error}
            </div>
          )}

          <div className="space-y-4">
            <Label>Dashboard Widgets</Label>
            <p className="text-xs text-muted-foreground">
              Select which widgets you want to display on your dashboard.
            </p>
            <div className="grid gap-2 sm:grid-cols-2">
              {DASHBOARD_WIDGETS.map((widget) => (
                <label
                  key={widget.id}
                  className={cn(
                    'flex cursor-pointer items-start gap-3 rounded-lg border p-3 text-sm transition-colors',
                    selectedWidgets.includes(widget.id)
                      ? 'border-primary bg-primary/5 text-primary'
                      : 'border-input hover:bg-muted'
                  )}
                >
                  <input
                    type="checkbox"
                    checked={selectedWidgets.includes(widget.id)}
                    onChange={() => toggleWidget(widget.id)}
                    className="mt-0.5 h-4 w-4"
                  />
                  <div>
                    <p className="font-medium">{widget.name}</p>
                    <p className="text-xs text-muted-foreground">{widget.description}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="timezone">Timezone</Label>
              <select
                id="timezone"
                value={form.timezone}
                onChange={(e) => setForm((prev) => ({ ...prev, timezone: e.target.value }))}
                className={cn(
                  'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                  'disabled:cursor-not-allowed disabled:opacity-50'
                )}
              >
                {TIMEZONES.map((tz) => (
                  <option key={tz} value={tz}>{tz}</option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="currency">Currency</Label>
              <select
                id="currency"
                value={form.currency}
                onChange={(e) => setForm((prev) => ({ ...prev, currency: e.target.value }))}
                className={cn(
                  'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                  'disabled:cursor-not-allowed disabled:opacity-50'
                )}
              >
                {CURRENCIES.map((cur) => (
                  <option key={cur} value={cur}>{cur}</option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="language">Language</Label>
              <select
                id="language"
                value={form.language}
                onChange={(e) => setForm((prev) => ({ ...prev, language: e.target.value }))}
                className={cn(
                  'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                  'disabled:cursor-not-allowed disabled:opacity-50'
                )}
              >
                {LANGUAGES.map((lang) => (
                  <option key={lang.code} value={lang.code}>{lang.name}</option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="email_digest">Email Digest</Label>
              <select
                id="email_digest"
                value={form.email_digest}
                onChange={(e) => setForm((prev) => ({ ...prev, email_digest: e.target.value }))}
                className={cn(
                  'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                  'disabled:cursor-not-allowed disabled:opacity-50'
                )}
              >
                {EMAIL_DIGESTS.map((d) => (
                  <option key={d.value} value={d.value}>{d.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex items-center gap-3 rounded-lg border p-4">
            <input
              type="checkbox"
              id="notifications_enabled"
              checked={form.notifications_enabled}
              onChange={(e) => setForm((prev) => ({ ...prev, notifications_enabled: e.target.checked }))}
              className="h-4 w-4"
            />
            <div>
              <Label htmlFor="notifications_enabled" className="cursor-pointer font-medium">
                Enable Notifications
              </Label>
              <p className="text-xs text-muted-foreground">
                Receive alerts for tender updates, bid deadlines, and important events.
              </p>
            </div>
          </div>

          <div className="flex justify-between gap-3 pt-4">
            <Button type="button" variant="outline" onClick={handleBack} disabled={loading}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
            <Button type="submit" disabled={loading}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Complete Setup
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
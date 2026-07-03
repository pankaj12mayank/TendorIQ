'use client';

import { useCallback, useEffect, useState } from 'react';
import { Plus, Save, Tag, Trash2 } from 'lucide-react';
import { appToast } from '@/lib/app-toast';

import { AdminRouteGuard } from '@/components/auth/admin-route-guard';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { LoadingState } from '@/components/ui/loading-state';
import { useAdminPlatform } from '@/hooks/use-admin-platform';

export default function AdminPricingPage() {
  const [name, setName] = useState('Professional');
  const [description, setDescription] = useState('');
  const [monthlyUsd, setMonthlyUsd] = useState(99);
  const [uploadLimit, setUploadLimit] = useState(500);
  const [expiryDays, setExpiryDays] = useState(30);
  const [popular, setPopular] = useState(true);
  const [active, setActive] = useState(true);
  const [features, setFeatures] = useState<string[]>(['']);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { loadSettings, saveBillingPricing } = useAdminPlatform();

  useEffect(() => {
    (async () => {
      try {
        const s = await loadSettings();
        const plan = (s?.pricing as any)?.plans?.[0];
        if (plan) {
          setName(plan.name || 'Professional');
          setDescription(plan.description || '');
          setMonthlyUsd(plan.monthly_usd || 99);
          setUploadLimit(plan.upload_limit || 500);
          setExpiryDays(plan.expiry_period_days || 30);
          setPopular(!!plan.popular);
          setActive(!!plan.active);
          setFeatures((plan.features || ['']).map((f: string) => f));
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load pricing');
      } finally {
        setLoading(false);
      }
    })();
  }, [loadSettings]);

  const updateFeature = (index: number, value: string) => {
    setFeatures((prev) => prev.map((f, i) => (i === index ? value : f)));
  };
  const addFeature = () => setFeatures((prev) => [...prev, '']);
  const removeFeature = (index: number) => setFeatures((prev) => prev.filter((_, i) => i !== index));

  const savePricing = useCallback(async () => {
    if (!name.trim()) { appToast.error('Plan name is required'); return; }
    if (!monthlyUsd || monthlyUsd <= 0) { appToast.error('Monthly price must be positive'); return; }
    setSaving(true);
    try {
      await saveBillingPricing({
        plan: {
          name: name.trim(),
          description: description.trim(),
          monthly_usd: Number(monthlyUsd),
          upload_limit: Number(uploadLimit),
          expiry_period_days: Number(expiryDays),
          popular,
          active,
          features: features.filter((f) => f.trim()),
        },
      });
      appToast.success('Pricing updated.');
    } catch (e) {
      appToast.error(e instanceof Error ? e.message : 'Pricing update failed');
    } finally {
      setSaving(false);
    }
  }, [name, description, monthlyUsd, uploadLimit, expiryDays, popular, active, features, saveBillingPricing]);

  if (loading) return <AdminRouteGuard><div className="w-full"><LoadingState message="Loading pricing..." /></div></AdminRouteGuard>;
  if (error) return <AdminRouteGuard><div className="w-full"><p className="text-sm text-destructive">{error}</p></div></AdminRouteGuard>;

  return (
    <AdminRouteGuard>
      <div className="w-full space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Pricing</h1>
          <p className="text-sm text-muted-foreground mt-1">Configure the subscription plan shown on the landing page and used for billing</p>
        </div>
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Tag className="h-4 w-4" />
              Plan details
            </CardTitle>
            <CardDescription>Edit the single subscription plan</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6 max-w-2xl">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="plan-name">Plan name</Label>
                <Input id="plan-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Professional" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="plan-desc">Description</Label>
                <Input id="plan-desc" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Complete workflow for tender analysis" />
              </div>
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="plan-price">Monthly price (USD)</Label>
                <Input id="plan-price" type="number" min={1} value={monthlyUsd} onChange={(e) => setMonthlyUsd(Number(e.target.value))} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="plan-upload-limit">Upload limit</Label>
                <Input id="plan-upload-limit" type="number" min={1} value={uploadLimit} onChange={(e) => setUploadLimit(Number(e.target.value))} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="plan-expiry">Expiry period (days)</Label>
                <Input id="plan-expiry" type="number" min={30} value={expiryDays} onChange={(e) => setExpiryDays(Number(e.target.value))} />
              </div>
            </div>
            <div className="flex gap-6">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={popular} onChange={(e) => setPopular(e.target.checked)} className="h-4 w-4 rounded border-gray-300" />
                <span className="text-sm font-medium">Popular</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={active} onChange={(e) => setActive(e.target.checked)} className="h-4 w-4 rounded border-gray-300" />
                <span className="text-sm font-medium">Active</span>
              </label>
            </div>
            <div className="space-y-3">
              <Label className="text-sm font-medium">Features</Label>
              {features.map((f, i) => (
                <div key={i} className="flex gap-2">
                  <Input value={f} onChange={(e) => updateFeature(i, e.target.value)} placeholder="e.g. 500 documents per cycle" className="flex-1" />
                  <Button variant="ghost" size="icon" onClick={() => removeFeature(i)} disabled={features.length <= 1}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
              <Button variant="outline" size="sm" onClick={addFeature}>
                <Plus className="mr-1 h-3 w-3" /> Add feature
              </Button>
            </div>
            <Button onClick={savePricing} disabled={saving}>
              <Save className="mr-1 h-4 w-4" />
              {saving ? 'Saving...' : 'Save pricing'}
            </Button>
          </CardContent>
        </Card>
      </div>
    </AdminRouteGuard>
  );
}
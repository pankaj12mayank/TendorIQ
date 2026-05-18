'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { useOnboardingApi, Step3Data, ExpertiseCategory } from '@/hooks/use-onboarding';
import { useOnboardingStore } from '@/stores/onboarding-store';
import { AlertCircle, Target, Loader2, ArrowLeft } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Checkbox } from '@/components/ui/checkbox';

const EXPERTISE_AREAS = [
  'Construction & Infrastructure',
  'Information Technology',
  'Healthcare & Medical',
  'Education & Training',
  'Transportation & Logistics',
  'Energy & Utilities',
  'Manufacturing & Industrial',
  'Professional Services',
  'Security & Defense',
  'Environmental Services',
  'Agriculture & Food',
  'Finance & Banking',
  'Communications',
  'Real Estate',
  'Other',
];

const TENDER_VOLUMES = [
  '1-10 per year', '11-25 per year', '26-50 per year',
  '51-100 per year', '100+ per year',
];

const CONTRACT_VALUES = [
  'Under $10,000', '$10,000 - $50,000', '$50,000 - $100,000',
  '$100,000 - $500,000', '$500,000 - $1,000,000', 'Over $1,000,000',
];

const TARGET_REGIONS = [
  { id: 'north_america', name: 'North America' },
  { id: 'europe', name: 'Europe' },
  { id: 'asia_pacific', name: 'Asia Pacific' },
  { id: 'middle_east', name: 'Middle East' },
  { id: 'africa', name: 'Africa' },
  { id: 'south_america', name: 'South America' },
  { id: 'global', name: 'Global' },
];

const CERTIFICATIONS = [
  'ISO 9001 (Quality Management)',
  'ISO 14001 (Environmental)',
  'ISO 27001 (Information Security)',
  'ISO 45001 (Occupational Health)',
  'SOC 2',
  'CMMI',
  'PMP',
  'Six Sigma',
  'ITIL',
  'Other',
];

export function Step3Expertise() {
  const router = useRouter();
  const store = useOnboardingStore();
  const { submitStep3, fetchExpertiseCategories, loading, error } = useOnboardingApi();

  const [form, setForm] = useState<Step3Data>({
    expertise_areas: (store.step3Data.expertise_areas as string[]) || [],
    custom_expertise: (store.step3Data.custom_expertise as string) || '',
    annual_tender_volume: (store.step3Data.annual_tender_volume as string) || '',
    average_contract_value: (store.step3Data.average_contract_value as string) || '',
    target_regions: (store.step3Data.target_regions as string[]) || [],
    certifications: (store.step3Data.certifications as string[]) || [],
  });

  const toggleArrayItem = <T extends string>(field: keyof Step3Data, item: T) => {
    setForm((prev) => {
      const arr = prev[field] as string[];
      return {
        ...prev,
        [field]: arr.includes(item) ? arr.filter((i) => i !== item) : [...arr, item],
      };
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await submitStep3(form);
      if (res.success) {
        store.setCurrentStep(4);
      }
    } catch {
      // Error handled by hook
    }
  };

  const handleBack = () => {
    store.setCurrentStep(2);
    router.push('/onboarding');
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Target className="h-6 w-6 text-primary" />
          <CardTitle>Tender Expertise</CardTitle>
        </div>
        <CardDescription>
          Help us understand your tender experience and specialization areas.
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

          <div className="space-y-3">
            <Label>Areas of Expertise <span className="text-destructive">*</span></Label>
            <p className="text-xs text-muted-foreground">Select all areas where you have tender experience.</p>
            <div className="grid gap-2 sm:grid-cols-2 md:grid-cols-3">
              {EXPERTISE_AREAS.map((area) => (
                <label
                  key={area}
                  className={cn(
                    'flex cursor-pointer items-center gap-2 rounded-lg border p-3 text-sm transition-colors',
                    form.expertise_areas.includes(area)
                      ? 'border-primary bg-primary/5 text-primary'
                      : 'border-input hover:bg-muted'
                  )}
                >
                  <Checkbox
                    checked={form.expertise_areas.includes(area)}
                    onCheckedChange={() => toggleArrayItem('expertise_areas', area)}
                  />
                  {area}
                </label>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="custom_expertise">Other Expertise (Optional)</Label>
            <Input
              id="custom_expertise"
              placeholder="Describe any other areas of expertise..."
              value={form.custom_expertise || ''}
              onChange={(e) => setForm((prev) => ({ ...prev, custom_expertise: e.target.value }))}
              maxLength={500}
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="annual_tender_volume">Annual Tender Volume</Label>
              <select
                id="annual_tender_volume"
                value={form.annual_tender_volume || ''}
                onChange={(e) => setForm((prev) => ({ ...prev, annual_tender_volume: e.target.value }))}
                className={cn(
                  'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                  'disabled:cursor-not-allowed disabled:opacity-50'
                )}
              >
                <option value="">Select volume</option>
                {TENDER_VOLUMES.map((v) => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="average_contract_value">Average Contract Value</Label>
              <select
                id="average_contract_value"
                value={form.average_contract_value || ''}
                onChange={(e) => setForm((prev) => ({ ...prev, average_contract_value: e.target.value }))}
                className={cn(
                  'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                  'disabled:cursor-not-allowed disabled:opacity-50'
                )}
              >
                <option value="">Select value</option>
                {CONTRACT_VALUES.map((v) => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="space-y-3">
            <Label>Target Regions</Label>
            <div className="flex flex-wrap gap-2">
              {TARGET_REGIONS.map((region) => (
                <label
                  key={region.id}
                  className={cn(
                    'flex cursor-pointer items-center gap-2 rounded-full border px-4 py-1.5 text-sm transition-colors',
                    form.target_regions.includes(region.id)
                      ? 'border-primary bg-primary text-primary-foreground'
                      : 'border-input hover:bg-muted'
                  )}
                >
                  <Checkbox
                    checked={form.target_regions.includes(region.id)}
                    onCheckedChange={() => toggleArrayItem('target_regions', region.id)}
                    className="sr-only"
                  />
                  {region.name}
                </label>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            <Label>Certifications (Optional)</Label>
            <div className="grid gap-2 sm:grid-cols-2">
              {CERTIFICATIONS.map((cert) => (
                <label
                  key={cert}
                  className={cn(
                    'flex cursor-pointer items-center gap-2 rounded-lg border p-3 text-sm transition-colors',
                    form.certifications.includes(cert)
                      ? 'border-primary bg-primary/5 text-primary'
                      : 'border-input hover:bg-muted'
                  )}
                >
                  <Checkbox
                    checked={form.certifications.includes(cert)}
                    onCheckedChange={() => toggleArrayItem('certifications', cert)}
                  />
                  {cert}
                </label>
              ))}
            </div>
          </div>

          <div className="flex justify-between gap-3 pt-4">
            <Button type="button" variant="outline" onClick={handleBack} disabled={loading}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
            <Button type="submit" disabled={loading || form.expertise_areas.length === 0}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Continue
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
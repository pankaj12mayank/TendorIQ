'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { useOnboardingApi, Step2Data } from '@/hooks/use-onboarding';
import { useOnboardingStore } from '@/stores/onboarding-store';
import { AlertCircle, Building, Loader2, ArrowLeft } from 'lucide-react';
import { cn } from '@/lib/utils';

const INDUSTRIES = [
  'Government', 'Private', 'Non-Profit', 'Healthcare', 'Education',
  'Technology', 'Manufacturing', 'Construction', 'Finance', 'Retail',
  'Transportation', 'Energy', 'Media', 'Telecommunications', 'Other',
];

const COMPANY_SIZES = [
  '1-10 employees', '11-50 employees', '51-200 employees',
  '201-500 employees', '501-1000 employees', '1001-5000 employees', '5000+ employees',
];

export function Step2Profile() {
  const router = useRouter();
  const store = useOnboardingStore();
  const { submitStep2, loading, error } = useOnboardingApi();

  const [form, setForm] = useState<Step2Data>({
    description: (store.step2Data.description as string) || '',
    website: (store.step2Data.website as string) || '',
    industry: (store.step2Data.industry as string) || '',
    company_size: (store.step2Data.company_size as string) || '',
    founded_year: (store.step2Data.founded_year as number) | undefined,
    headquarters: (store.step2Data.headquarters as string) || '',
    phone: (store.step2Data.phone as string) || '',
    address: (store.step2Data.address as string) || '',
  });

  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const validate = (): boolean => {
    const errors: Record<string, string> = {};
    if (form.website && !/^https?:\/\/.+/.test(form.website)) {
      errors.website = 'Please enter a valid URL starting with http:// or https://';
    }
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const updateField = (field: keyof Step2Data, value: string | number | undefined) => {
    setForm((prev) => ({ ...prev, [field]: value || undefined }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    try {
      const res = await submitStep2(form);
      if (res.success) {
        store.setCurrentStep(3);
      }
    } catch {
      // Error handled by hook
    }
  };

  const handleBack = () => {
    store.setCurrentStep(1);
    router.push('/onboarding');
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Building className="h-6 w-6 text-primary" />
          <CardTitle>Company Profile</CardTitle>
        </div>
        <CardDescription>
          Tell us more about your company. This information helps us personalize your experience.
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

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="description">Company Description</Label>
              <textarea
                id="description"
                placeholder="Brief description of your company and what you do..."
                value={form.description || ''}
                onChange={(e) => updateField('description', e.target.value)}
                className={cn(
                  'flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background',
                  'placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                  'disabled:cursor-not-allowed disabled:opacity-50'
                )}
                maxLength={2000}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="website">Website</Label>
              <Input
                id="website"
                type="url"
                placeholder="https://example.com"
                value={form.website || ''}
                onChange={(e) => updateField('website', e.target.value)}
                className={fieldErrors.website ? 'border-destructive' : ''}
              />
              {fieldErrors.website && (
                <p className="text-xs text-destructive">{fieldErrors.website}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone">Phone</Label>
              <Input
                id="phone"
                type="tel"
                placeholder="+1 (555) 000-0000"
                value={form.phone || ''}
                onChange={(e) => updateField('phone', e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="industry">Industry</Label>
              <select
                id="industry"
                value={form.industry || ''}
                onChange={(e) => updateField('industry', e.target.value)}
                className={cn(
                  'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                  'disabled:cursor-not-allowed disabled:opacity-50'
                )}
              >
                <option value="">Select industry</option>
                {INDUSTRIES.map((ind) => (
                  <option key={ind} value={ind}>{ind}</option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="company_size">Company Size</Label>
              <select
                id="company_size"
                value={form.company_size || ''}
                onChange={(e) => updateField('company_size', e.target.value)}
                className={cn(
                  'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                  'disabled:cursor-not-allowed disabled:opacity-50'
                )}
              >
                <option value="">Select company size</option>
                {COMPANY_SIZES.map((size) => (
                  <option key={size} value={size}>{size}</option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="headquarters">Headquarters</Label>
              <Input
                id="headquarters"
                placeholder="City, Country"
                value={form.headquarters || ''}
                onChange={(e) => updateField('headquarters', e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="founded_year">Founded Year</Label>
              <Input
                id="founded_year"
                type="number"
                placeholder="2020"
                value={form.founded_year || ''}
                onChange={(e) => updateField('founded_year', parseInt(e.target.value) || undefined)}
                min={1800}
                max={2100}
              />
            </div>

            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="address">Address</Label>
              <Input
                id="address"
                placeholder="123 Business Street, City, State, ZIP"
                value={form.address || ''}
                onChange={(e) => updateField('address', e.target.value)}
              />
            </div>
          </div>

          <div className="flex justify-between gap-3 pt-4">
            <Button type="button" variant="outline" onClick={handleBack} disabled={loading}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
            <Button type="submit" disabled={loading}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Continue
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
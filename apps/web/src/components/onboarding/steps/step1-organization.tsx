'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { useOnboardingApi, Step1Data } from '@/hooks/use-onboarding';
import { useOnboardingStore } from '@/stores/onboarding-store';
import { AlertCircle, Building2, Loader2 } from 'lucide-react';

function generateSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .trim();
}

export function Step1Organization() {
  const router = useRouter();
  const store = useOnboardingStore();
  const { submitStep1, loading, error } = useOnboardingApi();

  const [form, setForm] = useState<Step1Data>({
    name: (store.step1Data.name as string) || '',
    slug: (store.step1Data.slug as string) || '',
  });
  const [slugEdited, setSlugEdited] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const validate = (): boolean => {
    const errors: Record<string, string> = {};
    if (!form.name || form.name.length < 2) {
      errors.name = 'Organization name must be at least 2 characters';
    }
    if (!form.slug || form.slug.length < 2) {
      errors.slug = 'Slug must be at least 2 characters';
    } else if (!/^[a-z0-9-]+$/.test(form.slug)) {
      errors.slug = 'Slug can only contain lowercase letters, numbers, and hyphens';
    }
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleNameChange = (value: string) => {
    setForm((prev) => {
      const newForm = { ...prev, name: value };
      if (!slugEdited) {
        newForm.slug = generateSlug(value);
      }
      return newForm;
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    try {
      const res = await submitStep1(form);
      if (res.success) {
        router.push('/onboarding');
      }
    } catch {
      // Error handled by hook
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Building2 className="h-6 w-6 text-primary" />
          <CardTitle>Create Your Organization</CardTitle>
        </div>
        <CardDescription>
          Start by creating your organization. This will be the workspace for your team.
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

          <div className="space-y-2">
            <Label htmlFor="name">
              Organization Name <span className="text-destructive">*</span>
            </Label>
            <Input
              id="name"
              placeholder="Acme Corporation"
              value={form.name}
              onChange={(e) => handleNameChange(e.target.value)}
              className={fieldErrors.name ? 'border-destructive' : ''}
              maxLength={255}
            />
            {fieldErrors.name && (
              <p className="text-xs text-destructive">{fieldErrors.name}</p>
            )}
            <p className="text-xs text-muted-foreground">
              This is how your organization will appear throughout the platform.
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="slug">
              URL Slug <span className="text-destructive">*</span>
            </Label>
            <div className="flex items-center">
              <span className="rounded-l-md border border-r-0 bg-muted px-3 py-2 text-sm text-muted-foreground">
                tenderiq.app/
              </span>
              <Input
                id="slug"
                placeholder="acme-corp"
                value={form.slug}
                onChange={(e) => {
                  setSlugEdited(true);
                  setForm((prev) => ({ ...prev, slug: e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '') }));
                }}
                className={`rounded-l-none ${fieldErrors.slug ? 'border-destructive' : ''}`}
                maxLength={100}
              />
            </div>
            {fieldErrors.slug && (
              <p className="text-xs text-destructive">{fieldErrors.slug}</p>
            )}
            <p className="text-xs text-muted-foreground">
              Used in URLs and public references. Lowercase letters, numbers, and hyphens only.
            </p>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button type="submit" disabled={loading}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Create Organization
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
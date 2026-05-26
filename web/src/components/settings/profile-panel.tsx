'use client';

import { useEffect, useState } from 'react';
import { toast } from 'sonner';

import { useCurrentUser } from '@/hooks/use-auth';
import { useCompanyProfile, useUpdateCompanyProfile } from '@/hooks/use-company-profile';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export function ProfilePanel() {
  const user = useCurrentUser();
  const { data: company, isLoading } = useCompanyProfile();
  const updateCompany = useUpdateCompanyProfile();
  const [companyName, setCompanyName] = useState('');
  const [industry, setIndustry] = useState('');
  const [address, setAddress] = useState('');
  const [phone, setPhone] = useState('');
  const [website, setWebsite] = useState('');

  useEffect(() => {
    if (company) {
      setCompanyName(company.company_name ?? '');
      setIndustry(company.industry ?? '');
      setAddress(company.address ?? '');
      setPhone(company.phone ?? '');
      setWebsite(company.website ?? '');
    }
  }, [company]);

  const saveCompany = async () => {
    try {
      await updateCompany.mutateAsync({
        company_name: companyName || undefined,
        industry: industry || undefined,
        address: address || undefined,
        phone: phone || undefined,
        website: website || undefined,
      });
      toast.success('Company profile saved');
    } catch {
      toast.error('Failed to save company profile');
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <Card>
        <CardHeader>
          <CardTitle>Account</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p>
            <span className="text-muted-foreground">Name:</span> {user?.name ?? '—'}
          </p>
          <p>
            <span className="text-muted-foreground">Email:</span> {user?.email ?? '—'}
          </p>
          <p>
            <span className="text-muted-foreground">Role:</span> {user?.role ?? '—'}
          </p>
        </CardContent>
      </Card>
      <Card id="company">
        <CardHeader>
          <CardTitle>Company profile</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : (
            <>
              <div className="space-y-2">
                <Label htmlFor="company_name">Company name</Label>
                <Input
                  id="company_name"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="Your company"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="industry">Industry</Label>
                <Input id="industry" value={industry} onChange={(e) => setIndustry(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="address">Address</Label>
                <Input id="address" value={address} onChange={(e) => setAddress(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone">Phone</Label>
                <Input id="phone" value={phone} onChange={(e) => setPhone(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="website">Website</Label>
                <Input id="website" value={website} onChange={(e) => setWebsite(e.target.value)} />
              </div>
              <Button onClick={saveCompany} disabled={updateCompany.isPending}>
                {updateCompany.isPending ? 'Saving…' : 'Save company'}
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

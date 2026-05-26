'use client';

import { useEffect, useState } from 'react';
import { toast } from 'sonner';

import { useCurrentUser } from '@/hooks/use-auth';
import { useCompanyProfile, useUpdateCompanyProfile } from '@/hooks/use-company-profile';
import { apiUrl } from '@/lib/api-config';
import { buildApiAuthHeaders } from '@/lib/auth-user';
import { getStoredSession } from '@/lib/auth-session';
import { getAuthProvider } from '@/lib/supabase-config';
import { PasswordInput } from '@/components/ui/password-input';
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
  const isLocalAuth = getAuthProvider() === 'local';
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [changingPassword, setChangingPassword] = useState(false);

  useEffect(() => {
    if (company) {
      setCompanyName(company.company_name ?? '');
      setIndustry(company.industry ?? '');
      setAddress(company.address ?? '');
      setPhone(company.phone ?? '');
      setWebsite(company.website ?? '');
    }
  }, [company]);

  const changePassword = async () => {
    if (newPassword.length < 8) {
      toast.error('New password must be at least 8 characters');
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }
    const token = getStoredSession()?.token;
    if (!token) {
      toast.error('Sign in again to change your password');
      return;
    }
    setChangingPassword(true);
    try {
      const res = await fetch(apiUrl('/auth/change-password'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...buildApiAuthHeaders(token, user ?? undefined),
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = (body as { detail?: string }).detail;
        throw new Error(typeof detail === 'string' ? detail : 'Password change failed');
      }
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      toast.success('Password updated');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Password change failed');
    } finally {
      setChangingPassword(false);
    }
  };

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
      {isLocalAuth && (
        <Card>
          <CardHeader>
            <CardTitle>Change password</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Updates your login password in the database. Use this after first sign-in with the
              default from <code className="text-xs">.tenderiq/owner-account.txt</code>.
            </p>
            <div className="space-y-2">
              <Label htmlFor="current_password">Current password</Label>
              <PasswordInput
                id="current_password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                autoComplete="current-password"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new_password">New password</Label>
              <PasswordInput
                id="new_password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                autoComplete="new-password"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm_password">Confirm new password</Label>
              <PasswordInput
                id="confirm_password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
              />
            </div>
            <Button onClick={changePassword} disabled={changingPassword}>
              {changingPassword ? 'Updating…' : 'Update password'}
            </Button>
          </CardContent>
        </Card>
      )}
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

'use client';

import { useEffect, useState } from 'react';
import { appToast } from '@/lib/app-toast';

import { useCurrentUser } from '@/hooks/use-auth';
import { useCompanyProfile, useUpdateCompanyProfile } from '@/hooks/use-company-profile';
import { api } from '@/lib/api-client';
import { parseApiErrorMessage } from '@/lib/api-envelope';
import { getAuthProvider } from '@/lib/auth-provider';
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
      appToast.warning('New password must be at least 8 characters.');
      return;
    }
    if (newPassword !== confirmPassword) {
      appToast.warning('New passwords do not match.');
      return;
    }
    if (!currentPassword.trim()) {
      appToast.warning('Enter your current password.');
      return;
    }
    setChangingPassword(true);
    try {
      await api.post('/api/v1/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      appToast.success('Password updated. Use your new password on the next sign-in.');
    } catch (err) {
      const message =
        err instanceof Error && err.message ? err.message : 'Password change failed';
      appToast.error(message);
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
      appToast.success('Company profile saved.');
    } catch {
      appToast.error('Failed to save company profile.');
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
      <Card>
        <CardHeader>
          <CardTitle>Change password</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {!isLocalAuth ? (
            <p className="text-sm text-muted-foreground">
              Password is managed by your external sign-in provider. Use that provider to change your
              password.
            </p>
          ) : (
            <>
              <p className="text-sm text-muted-foreground">
                Set a new password for this account. After saving, sign in with your email and the
                new password.
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
              <Button
                onClick={() => void changePassword()}
                disabled={changingPassword || !currentPassword || !newPassword}
              >
                {changingPassword ? 'Updating…' : 'Update password'}
              </Button>
            </>
          )}
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

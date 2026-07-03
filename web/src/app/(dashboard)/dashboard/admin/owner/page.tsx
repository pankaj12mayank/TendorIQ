'use client';

import { useEffect, useState } from 'react';
import { Image, Key, Save, Upload, User } from 'lucide-react';
import { appToast } from '@/lib/app-toast';

import { AdminRouteGuard } from '@/components/auth/admin-route-guard';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { LoadingState } from '@/components/ui/loading-state';
import { useAdminPlatform } from '@/hooks/use-admin-platform';

export default function AdminOwnerPage() {
  const [ownerProfile, setOwnerProfile] = useState<Record<string, unknown> | null>(null);
  const [ownerPassword, setOwnerPassword] = useState('');
  const [ownerUsername, setOwnerUsername] = useState('');
  const [uploadingKind, setUploadingKind] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { saving, loadOwnerProfile, saveOwnerProfile, uploadOwnerAsset } = useAdminPlatform();

  useEffect(() => {
    (async () => {
      try {
        const ownerRes = await loadOwnerProfile();
        setOwnerProfile(ownerRes);
        setOwnerUsername(String(ownerRes.username ?? ''));
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load owner data');
      } finally {
        setLoading(false);
      }
    })();
  }, [loadOwnerProfile]);

  if (loading) return <AdminRouteGuard><div className="w-full"><LoadingState message="Loading owner profile..." /></div></AdminRouteGuard>;
  if (error) return <AdminRouteGuard><div className="w-full"><p className="text-sm text-destructive">{error}</p></div></AdminRouteGuard>;

  return (
    <AdminRouteGuard>
      <div className="w-full space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Owner profile</h1>
          <p className="text-sm text-muted-foreground mt-1">Manage system owner credentials and branding assets</p>
        </div>
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <User className="h-4 w-4" />
              Account credentials
            </CardTitle>
            <CardDescription>Update the super admin username and password</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 max-w-xl">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="owner-username">Username</Label>
                <Input id="owner-username" value={ownerUsername} onChange={(e) => setOwnerUsername(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="owner-password">
                  <span className="flex items-center gap-1">
                    <Key className="h-3 w-3" />
                    New password
                  </span>
                </Label>
                <Input id="owner-password" type="password" value={ownerPassword} onChange={(e) => setOwnerPassword(e.target.value)} placeholder="Leave blank to keep current" />
              </div>
            </div>
            <Button
              loading={saving}
              disabled={saving}
              onClick={async () => {
                const toastId = appToast.loading('Saving owner profile...');
                await saveOwnerProfile({
                  username: ownerUsername,
                  ...(ownerPassword ? { password: ownerPassword } : {}),
                });
                setOwnerPassword('');
                appToast.dismiss(toastId);
                appToast.success('Owner profile updated.');
                const latest = await loadOwnerProfile();
                setOwnerProfile(latest);
              }}
            >
              <Save className="mr-1 h-4 w-4" />
              Save profile
            </Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Image className="h-4 w-4" />
              Branding assets
            </CardTitle>
            <CardDescription>Upload avatar, logo, and favicon images</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              {(['avatar', 'logo', 'favicon'] as const).map((kind) => (
                <div key={kind} className="rounded-lg border p-4 space-y-3">
                  <Label className="text-sm font-medium capitalize block">{kind}</Label>
                  <div className="flex items-center gap-3">
                    {Boolean(ownerProfile?.[`${kind}_url`]) && (
                      <img src={ownerProfile?.[`${kind}_url`] as string} alt={kind} className="h-12 w-12 rounded-lg object-cover border" />
                    )}
                    <div className="flex-1">
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={uploadingKind === kind}
                        className="w-full"
                        onClick={() => {
                          const input = document.createElement('input');
                          input.type = 'file';
                          input.accept = 'image/*';
                          input.onchange = async (e) => {
                            const file = (e.target as HTMLInputElement).files?.[0];
                            if (!file) return;
                            setUploadingKind(kind);
                            try {
                              await uploadOwnerAsset(kind, file);
                              const latest = await loadOwnerProfile();
                              setOwnerProfile(latest);
                              appToast.success(`${kind} updated.`);
                            } catch (err) {
                              appToast.error(err instanceof Error ? err.message : 'Upload failed');
                            } finally {
                              setUploadingKind(null);
                            }
                          };
                          input.click();
                        }}
                      >
                        <Upload className="mr-1 h-3 w-3" />
                        {uploadingKind === kind ? 'Uploading...' : 'Upload'}
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </AdminRouteGuard>
  );
}
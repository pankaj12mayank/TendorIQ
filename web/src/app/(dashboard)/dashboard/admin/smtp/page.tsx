'use client';

import { useEffect, useState } from 'react';
import { Mail, Save, Send, Settings } from 'lucide-react';
import { appToast } from '@/lib/app-toast';

import { AdminRouteGuard } from '@/components/auth/admin-route-guard';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { LoadingState } from '@/components/ui/loading-state';
import { useAdminPlatform } from '@/hooks/use-admin-platform';

export default function AdminSmtpPage() {
  const [smtp, setSmtp] = useState({ host: '', port: 587, sender_email: '', sender_name: 'TenderIQ', app_password: '' });
  const [smtpTestEmail, setSmtpTestEmail] = useState('');
  const [smtpTesting, setSmtpTesting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { saving, loadSmtpSettings, saveSmtpSettings, testSmtpSettings } = useAdminPlatform();

  useEffect(() => {
    (async () => {
      try {
        const smtpLoaded = await loadSmtpSettings();
        setSmtp({
          host: String(smtpLoaded.host ?? ''),
          port: Number(smtpLoaded.port ?? 587),
          sender_email: String(smtpLoaded.sender_email ?? ''),
          sender_name: String(smtpLoaded.sender_name ?? 'TenderIQ'),
          app_password: '',
        });
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load SMTP settings');
      } finally {
        setLoading(false);
      }
    })();
  }, [loadSmtpSettings]);

  if (loading) return <AdminRouteGuard><div className="w-full"><LoadingState message="Loading SMTP settings..." /></div></AdminRouteGuard>;
  if (error) return <AdminRouteGuard><div className="w-full"><p className="text-sm text-destructive">{error}</p></div></AdminRouteGuard>;

  return (
    <AdminRouteGuard>
      <div className="w-full space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">SMTP settings</h1>
          <p className="text-sm text-muted-foreground mt-1">Configure outbound email server for notifications</p>
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Settings className="h-4 w-4" />
                Server configuration
              </CardTitle>
              <CardDescription>Enter your SMTP server details</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="smtp-host">SMTP host</Label>
                  <Input id="smtp-host" value={smtp.host} onChange={(e) => setSmtp((s) => ({ ...s, host: e.target.value }))} placeholder="smtp.gmail.com" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="smtp-port">SMTP port</Label>
                  <Input id="smtp-port" type="number" value={smtp.port} onChange={(e) => setSmtp((s) => ({ ...s, port: Number(e.target.value || 587) }))} />
                </div>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="smtp-sender-email">Sender email</Label>
                  <Input id="smtp-sender-email" type="email" value={smtp.sender_email} onChange={(e) => setSmtp((s) => ({ ...s, sender_email: e.target.value }))} placeholder="noreply@company.com" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="smtp-sender-name">Sender name</Label>
                  <Input id="smtp-sender-name" value={smtp.sender_name} onChange={(e) => setSmtp((s) => ({ ...s, sender_name: e.target.value }))} />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="smtp-app-password">App password</Label>
                <Input id="smtp-app-password" type="password" value={smtp.app_password} onChange={(e) => setSmtp((s) => ({ ...s, app_password: e.target.value }))} placeholder="App password or SMTP password" />
              </div>
              <Button loading={saving} disabled={saving} onClick={async () => {
                try { await saveSmtpSettings(smtp); appToast.success('SMTP settings saved.'); } catch (e) { appToast.error(e instanceof Error ? e.message : 'Failed to save SMTP settings'); }
              }}>
                <Save className="mr-1 h-4 w-4" />
                Save settings
              </Button>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Send className="h-4 w-4" />
                Test email
              </CardTitle>
              <CardDescription>Send a test message to verify your configuration</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-lg border bg-muted/30 p-4">
                <p className="text-xs text-muted-foreground mb-3">
                  Enter a recipient email address and send a test message to verify your SMTP configuration is working correctly.
                </p>
                <div className="flex gap-2">
                  <Input
                    type="email"
                    placeholder="test@yourdomain.com"
                    value={smtpTestEmail}
                    onChange={(e) => setSmtpTestEmail(e.target.value)}
                    className="flex-1"
                  />
                  <Button
                    variant="outline"
                    disabled={smtpTesting || !smtpTestEmail}
                    onClick={async () => {
                      setSmtpTesting(true);
                      try {
                        await testSmtpSettings(smtpTestEmail);
                        appToast.success('SMTP test email sent.');
                      } catch (e) {
                        appToast.error(e instanceof Error ? e.message : 'SMTP test failed');
                      } finally {
                        setSmtpTesting(false);
                      }
                    }}
                  >
                    <Mail className="mr-1 h-3 w-3" />
                    {smtpTesting ? 'Sending...' : 'Send test'}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </AdminRouteGuard>
  );
}
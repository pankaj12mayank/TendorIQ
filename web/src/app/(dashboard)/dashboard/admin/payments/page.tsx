'use client';

import { useCallback, useEffect, useState } from 'react';
import { CreditCard, DollarSign, RefreshCw, ShieldAlert } from 'lucide-react';
import { appToast } from '@/lib/app-toast';

import { AdminRouteGuard } from '@/components/auth/admin-route-guard';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { LoadingState } from '@/components/ui/loading-state';
import {
  DataTableShell,
  DataTable,
  DataTableHeader,
  DataTableHead,
  DataTableBody,
  DataTableRow,
  DataTableCell,
} from '@/components/design-system/data-table';
import { KpiCard } from '@/components/design-system/kpi-card';
import { useAdminPlatform } from '@/hooks/use-admin-platform';

export default function AdminPaymentsPage() {
  const [paymentSettings, setPaymentSettings] = useState<Record<string, unknown>>({});
  const [paymentHistory, setPaymentHistory] = useState<any>(null);
  const [paymentStatusFilter, setPaymentStatusFilter] = useState('');
  const [paymentProviderFilter, setPaymentProviderFilter] = useState('');
  const [paymentPage, setPaymentPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { saving, loadPaymentSettings, savePaymentSettings, testPaymentSettings, loadPaymentHistory } = useAdminPlatform();

  useEffect(() => {
    (async () => {
      try {
        const cfg = await loadPaymentSettings();
        setPaymentSettings(cfg);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load payment settings');
      } finally {
        setLoading(false);
      }
    })();
  }, [loadPaymentSettings]);

  const loadPayments = useCallback(async () => {
    const hist = await loadPaymentHistory({
      page: paymentPage, limit: 25,
      status: paymentStatusFilter || undefined,
      provider: paymentProviderFilter || undefined,
    }) as any;
    setPaymentHistory(hist);
  }, [loadPaymentHistory, paymentPage, paymentProviderFilter, paymentStatusFilter]);

  useEffect(() => { if (loading) return; void loadPayments(); }, [loading, loadPayments]);

  if (loading) return <AdminRouteGuard><div className="w-full"><LoadingState message="Loading payment settings..." /></div></AdminRouteGuard>;
  if (error) return <AdminRouteGuard><div className="w-full"><p className="text-sm text-destructive">{error}</p></div></AdminRouteGuard>;

  const rows = (paymentHistory?.data ?? []) as any[];
  const pagination = paymentHistory?.pagination ?? {};

  return (
    <AdminRouteGuard>
      <div className="w-full space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Payments</h1>
          <p className="text-sm text-muted-foreground mt-1">Manage payment gateways and view transaction history</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-3">
          <KpiCard title="Revenue" value={`$${Number(paymentHistory?.cards?.total_revenue ?? 0).toLocaleString('en-US')}`} icon={DollarSign} />
          <KpiCard title="Failed payments" value={String(paymentHistory?.cards?.failed_count ?? 0)} icon={ShieldAlert} />
          <KpiCard title="Renewals" value={String(paymentHistory?.cards?.renewals_count ?? 0)} icon={RefreshCw} />
        </div>
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <CreditCard className="h-4 w-4" />
              Payment gateways
            </CardTitle>
            <CardDescription>Configure Razorpay and Stripe API keys</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-3 rounded-lg border p-4">
                <h4 className="text-sm font-semibold">Razorpay</h4>
                <div className="space-y-2">
                  <Label className="text-xs">Key ID</Label>
                  <Input size={1} value={String(paymentSettings.razorpay_key_id ?? '')} onChange={(e) => setPaymentSettings((s) => ({ ...s, razorpay_key_id: e.target.value }))} placeholder="rzp_live_..." />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">Key secret</Label>
                  <Input size={1} type="password" value={String(paymentSettings.razorpay_key_secret ?? '')} onChange={(e) => setPaymentSettings((s) => ({ ...s, razorpay_key_secret: e.target.value }))} placeholder="••••••••" />
                </div>
                <Button variant="outline" size="sm" onClick={() => testPaymentSettings('razorpay')}>Test connection</Button>
              </div>
              <div className="space-y-3 rounded-lg border p-4">
                <h4 className="text-sm font-semibold">Stripe</h4>
                <div className="space-y-2">
                  <Label className="text-xs">Publishable key</Label>
                  <Input size={1} value={String(paymentSettings.stripe_publishable_key ?? '')} onChange={(e) => setPaymentSettings((s) => ({ ...s, stripe_publishable_key: e.target.value }))} placeholder="pk_live_..." />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">Secret key</Label>
                  <Input size={1} type="password" value={String(paymentSettings.stripe_secret_key ?? '')} onChange={(e) => setPaymentSettings((s) => ({ ...s, stripe_secret_key: e.target.value }))} placeholder="sk_live_..." />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">Webhook secret</Label>
                  <Input size={1} type="password" value={String(paymentSettings.stripe_webhook_secret ?? '')} onChange={(e) => setPaymentSettings((s) => ({ ...s, stripe_webhook_secret: e.target.value }))} placeholder="whsec_..." />
                </div>
                <Button variant="outline" size="sm" onClick={() => testPaymentSettings('stripe')}>Test connection</Button>
              </div>
            </div>
            <Button loading={saving} disabled={saving} onClick={async () => { await savePaymentSettings(paymentSettings); appToast.success('Payment settings saved.'); }}>
              Save gateway settings
            </Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <CardTitle className="text-base">Payment history</CardTitle>
                <CardDescription>All transactions across all tenants</CardDescription>
              </div>
              <div className="flex gap-2">
                <Input
                  placeholder="Filter by status..."
                  value={paymentStatusFilter}
                  onChange={(e) => { setPaymentStatusFilter(e.target.value); setPaymentPage(1); }}
                  className="w-36 h-8 text-xs"
                />
                <Input
                  placeholder="Filter by provider..."
                  value={paymentProviderFilter}
                  onChange={(e) => { setPaymentProviderFilter(e.target.value); setPaymentPage(1); }}
                  className="w-36 h-8 text-xs"
                />
                <Button variant="outline" size="sm" onClick={() => void loadPayments()}>
                  <RefreshCw className="mr-1 h-3 w-3" />
                  Refresh
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <DataTableShell>
              <DataTable>
                <DataTableHeader>
                  <DataTableRow>
                    <DataTableHead>ID</DataTableHead>
                    <DataTableHead>Provider</DataTableHead>
                    <DataTableHead>Plan</DataTableHead>
                    <DataTableHead>Amount</DataTableHead>
                    <DataTableHead>Status</DataTableHead>
                    <DataTableHead>Date</DataTableHead>
                  </DataTableRow>
                </DataTableHeader>
                <DataTableBody>
                  {rows.map((p: any) => (
                    <DataTableRow key={p.id}>
                      <DataTableCell className="font-mono text-xs">{p.id?.slice(0, 12)}…</DataTableCell>
                      <DataTableCell className="capitalize">{p.provider}</DataTableCell>
                      <DataTableCell>{p.plan || '—'}</DataTableCell>
                      <DataTableCell>${Number(p.amount || 0).toLocaleString('en-US')}</DataTableCell>
                      <DataTableCell>
                        <Badge variant={p.status === 'paid' ? 'success' : p.status === 'failed' ? 'destructive' : 'warning'} className="text-xs capitalize">
                          {p.status}
                        </Badge>
                      </DataTableCell>
                      <DataTableCell className="text-muted-foreground">
                        {p.created_at ? new Date(p.created_at).toLocaleDateString() : '—'}
                      </DataTableCell>
                    </DataTableRow>
                  ))}
                  {rows.length === 0 && (
                    <DataTableRow>
                      <DataTableCell colSpan={6} className="text-center text-muted-foreground py-8">
                        No payments found.
                      </DataTableCell>
                    </DataTableRow>
                  )}
                </DataTableBody>
              </DataTable>
            </DataTableShell>
            {Number(pagination.pages ?? 0) > 1 && (
              <div className="flex items-center justify-between mt-4 text-sm">
                <span className="text-muted-foreground">
                  Page {paymentPage} of {pagination.pages}
                </span>
                <div className="flex items-center gap-2">
                  <Button size="sm" variant="outline" disabled={paymentPage <= 1} onClick={() => setPaymentPage((p) => Math.max(1, p - 1))}>
                    Previous
                  </Button>
                  <Button size="sm" variant="outline" disabled={paymentPage >= Number(pagination.pages)} onClick={() => setPaymentPage((p) => Math.min(Number(pagination.pages), p + 1))}>
                    Next
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </AdminRouteGuard>
  );
}
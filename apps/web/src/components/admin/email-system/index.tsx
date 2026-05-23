'use client';

import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Mail,
  Zap,
  Server,
  FileText,
  BarChart3,
  List,
  Palette,
  Play,
  Copy,
  Archive,
  Check,
  X,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PasswordInput } from '@/components/ui/password-input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { KpiCard } from '@/components/design-system';
import { useEmailSystem, type EmailQueueRow, type EmailTemplate } from '@/hooks/use-email-system';
import { cn } from '@/lib/utils';
import { staggerContainer, staggerItem } from '@/design-system/motion';

const VARIABLE_HINTS = ['user_name', 'company_name', 'reset_link', 'document_name', 'plan_name', 'dashboard_link', 'billing_link'];

export function EmailSystem() {
  const {
    loading,
    templates,
    events,
    analytics,
    logs,
    queue,
    smtpConfigs,
    fetchTemplates,
    fetchEvents,
    fetchAnalytics,
    fetchLogs,
    fetchQueue,
    fetchSmtp,
    createTemplate,
    updateTemplate,
    activateTemplate,
    deactivateTemplate,
    archiveTemplate,
    duplicateTemplate,
    testSend,
    previewTemplate,
    updateEvent,
    saveSmtp,
    testSmtp,
    retryQueueItem,
  } = useEmailSystem();

  const [tab, setTab] = useState('templates');
  const [selected, setSelected] = useState<EmailTemplate | null>(null);
  const [previewHtml, setPreviewHtml] = useState('');
  const [testEmail, setTestEmail] = useState('');
  const [smtpForm, setSmtpForm] = useState({
    name: 'Primary SMTP',
    provider: 'smtp',
    host: '',
    port: 587,
    username: '',
    password: '',
    from_email: '',
    from_name: 'TenderIQ',
    is_primary: true,
  });

  useEffect(() => {
    fetchTemplates();
    fetchEvents();
    fetchAnalytics();
    fetchLogs();
    fetchQueue();
    fetchSmtp();
  }, [fetchTemplates, fetchEvents, fetchAnalytics, fetchLogs, fetchQueue, fetchSmtp]);

  const stalledProcessing = useMemo(() => {
    const cutoff = Date.now() - 5 * 60 * 1000;
    return queue.filter((q) => {
      if (q.status !== 'processing') return false;
      if (!q.created_at) return true;
      const ts = Date.parse(q.created_at);
      return Number.isNaN(ts) || ts < cutoff;
    });
  }, [queue]);

  useEffect(() => {
    const processing = analytics?.queue_processing ?? 0;
    if (processing <= 0 && stalledProcessing.length === 0) return;
    const id = window.setInterval(() => {
      void fetchQueue();
      void fetchAnalytics();
    }, 30_000);
    return () => window.clearInterval(id);
  }, [analytics?.queue_processing, stalledProcessing.length, fetchQueue, fetchAnalytics]);

  useEffect(() => {
    if (templates.length && !selected) {
      setSelected(templates[0]);
    }
  }, [templates, selected]);

  const handlePreview = async () => {
    if (!selected) return;
    const res = await previewTemplate(selected.subject, selected.html_body, {
      user_name: 'Alex Morgan',
      company_name: 'TenderIQ',
      dashboard_link: 'http://localhost:3000/dashboard',
      reset_link: 'http://localhost:3000/reset-password?token=preview',
    });
    setPreviewHtml(res.html);
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h2 className="text-2xl font-display font-bold">Email System</h2>
        <p className="text-muted-foreground text-sm mt-1">
          Event-driven transactional email — templates are never hard-deleted.
        </p>
      </div>

      {(analytics?.queue_processing ?? 0) > 0 || stalledProcessing.length > 0 ? (
        <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm">
          <p className="font-medium text-amber-900 dark:text-amber-100">
            {stalledProcessing.length > 0
              ? `${stalledProcessing.length} queue item(s) stuck in processing`
              : `${analytics?.queue_processing ?? 0} item(s) processing`}
          </p>
          <p className="text-muted-foreground mt-1">
            Queue refreshes every 30s. Use Retry on stalled rows or open the Queue tab.
          </p>
        </div>
      ) : null}

      <motion.div variants={staggerContainer} initial="initial" animate="animate" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <motion.div variants={staggerItem}>
          <KpiCard title="Sent (30d)" value={String(analytics?.sent ?? 0)} icon={Mail} />
        </motion.div>
        <motion.div variants={staggerItem}>
          <KpiCard title="Delivery rate" value={`${analytics?.delivery_rate ?? 0}%`} icon={Zap} trendUp />
        </motion.div>
        <motion.div variants={staggerItem}>
          <KpiCard title="Queue pending" value={String(analytics?.queue_pending ?? 0)} icon={List} />
        </motion.div>
        <motion.div variants={staggerItem}>
          <KpiCard title="Failure rate" value={`${analytics?.failure_rate ?? 0}%`} icon={BarChart3} trendUp={!(analytics && analytics.failure_rate > 5)} />
        </motion.div>
      </motion.div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="flex flex-wrap h-auto gap-1">
          <TabsTrigger value="templates">Templates</TabsTrigger>
          <TabsTrigger value="events">Events</TabsTrigger>
          <TabsTrigger value="smtp">SMTP</TabsTrigger>
          <TabsTrigger value="logs">Logs</TabsTrigger>
          <TabsTrigger value="queue">Queue</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="templates" className="mt-4 space-y-4">
          <div className="grid lg:grid-cols-3 gap-4">
            <Card className="surface-card lg:col-span-1">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-base">Templates</CardTitle>
                <Button
                  size="sm"
                  onClick={() =>
                    createTemplate({
                      slug: `template-${Date.now()}`,
                      name: 'New Template',
                      subject: 'Subject with {{user_name}}',
                      html_body: '<p>Hello {{user_name}},</p>',
                    })
                  }
                >
                  New
                </Button>
              </CardHeader>
              <CardContent className="space-y-2 max-h-[480px] overflow-y-auto scroll-premium">
                {templates.map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setSelected(t)}
                    className={cn(
                      'w-full text-left rounded-lg border p-3 transition-all',
                      selected?.id === t.id ? 'border-primary bg-primary/5' : 'border-border/60 hover:border-primary/30'
                    )}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-medium text-sm truncate">{t.name}</span>
                      <StatusBadge status={t.status} />
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">{t.slug}</p>
                  </button>
                ))}
              </CardContent>
            </Card>

            {selected && (
              <Card className="surface-card lg:col-span-2">
                <CardHeader>
                  <CardTitle>{selected.name}</CardTitle>
                  <CardDescription>v{selected.version} · Use {'{{variable}}'} syntax</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid sm:grid-cols-2 gap-3">
                    <div>
                      <Label>Name</Label>
                      <Input
                        value={selected.name}
                        onChange={(e) => setSelected({ ...selected, name: e.target.value })}
                      />
                    </div>
                    <div>
                      <Label>Slug</Label>
                      <Input value={selected.slug} disabled className="opacity-60" />
                    </div>
                  </div>
                  <div>
                    <Label>Subject</Label>
                    <Input
                      value={selected.subject}
                      onChange={(e) => setSelected({ ...selected, subject: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>HTML body</Label>
                    <Textarea
                      className="min-h-[200px] font-mono text-xs"
                      value={selected.html_body}
                      onChange={(e) => setSelected({ ...selected, html_body: e.target.value })}
                    />
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {VARIABLE_HINTS.map((v) => (
                      <Badge key={v} variant="outline" className="text-xs cursor-pointer" onClick={() => setSelected({
                        ...selected,
                        html_body: selected.html_body + `{{${v}}}`,
                      })}>
                        {`{{${v}}}`}
                      </Badge>
                    ))}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button onClick={() => updateTemplate(selected.id, selected)} disabled={loading}>
                      Save
                    </Button>
                    <Button variant="outline" onClick={handlePreview}>
                      <Play className="h-4 w-4" /> Preview
                    </Button>
                    {selected.status !== 'active' && (
                      <Button variant="secondary" onClick={() => activateTemplate(selected.id)}>
                        <Check className="h-4 w-4" /> Activate
                      </Button>
                    )}
                    {selected.status === 'active' && (
                      <Button variant="outline" onClick={() => deactivateTemplate(selected.id)}>
                        <X className="h-4 w-4" /> Deactivate
                      </Button>
                    )}
                    <Button variant="outline" onClick={() => duplicateTemplate(selected.id)}>
                      <Copy className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" onClick={() => archiveTemplate(selected.id)}>
                      <Archive className="h-4 w-4" /> Archive
                    </Button>
                  </div>
                  <div className="flex gap-2 items-end">
                    <div className="flex-1">
                      <Label>Test send to</Label>
                      <Input value={testEmail} onChange={(e) => setTestEmail(e.target.value)} placeholder="you@company.com" />
                    </div>
                    <Button
                      disabled={!testEmail}
                      onClick={() => testSend(testEmail, selected.id, { user_name: 'Test User' })}
                    >
                      Send test
                    </Button>
                  </div>
                  {previewHtml && (
                    <div className="rounded-lg border overflow-hidden">
                      <div className="text-xs text-muted-foreground px-3 py-2 border-b bg-muted/30">Live preview</div>
                      <iframe title="preview" srcDoc={previewHtml} className="w-full h-64 bg-white" />
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="events" className="mt-4">
          <Card className="surface-card">
            <CardHeader>
              <CardTitle>Event triggers</CardTitle>
              <CardDescription>Emails only send when event is enabled and template is active</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 max-h-[600px] overflow-y-auto">
              {events.map((ev) => (
                <div key={ev.event_key} className="flex flex-wrap items-center gap-3 rounded-lg border border-border/60 p-3">
                  <div className="flex-1 min-w-[200px]">
                    <p className="font-medium text-sm">{ev.name}</p>
                    <p className="text-xs text-muted-foreground font-mono">{ev.event_key}</p>
                  </div>
                  <Badge variant="outline">{ev.category}</Badge>
                  <Select
                    value={ev.template_id || ''}
                    onValueChange={(v) => updateEvent(ev.event_key, { template_id: v })}
                  >
                    <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Template" />
                    </SelectTrigger>
                    <SelectContent>
                      {templates.filter((t) => t.status !== 'archived').map((t) => (
                        <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button
                    size="sm"
                    variant={ev.is_enabled ? 'default' : 'outline'}
                    onClick={() => updateEvent(ev.event_key, { is_enabled: !ev.is_enabled })}
                  >
                    {ev.is_enabled ? 'Enabled' : 'Disabled'}
                  </Button>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="smtp" className="mt-4">
          <Card className="surface-card max-w-xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Server className="h-5 w-5" /> SMTP / Resend</CardTitle>
              <CardDescription>Credentials stored encrypted. Primary with automatic fallback.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {smtpConfigs.map((c: { id: string; name: string; provider: string; from_email: string; is_primary: boolean; last_test_status?: string }) => (
                <div key={c.id} className="flex items-center justify-between rounded-lg border p-3">
                  <div>
                    <p className="font-medium text-sm">{c.name}</p>
                    <p className="text-xs text-muted-foreground">{c.provider} · {c.from_email}</p>
                  </div>
                  <Button size="sm" variant="outline" onClick={() => testSmtp(c.id)}>
                    Test
                  </Button>
                </div>
              ))}
              <div className="grid gap-3 pt-2">
                <Input placeholder="SMTP host" value={smtpForm.host} onChange={(e) => setSmtpForm({ ...smtpForm, host: e.target.value })} />
                <Input placeholder="Port" type="number" value={smtpForm.port} onChange={(e) => setSmtpForm({ ...smtpForm, port: Number(e.target.value) })} />
                <Input placeholder="Username" value={smtpForm.username} onChange={(e) => setSmtpForm({ ...smtpForm, username: e.target.value })} />
                <PasswordInput placeholder="Password" value={smtpForm.password} onChange={(e) => setSmtpForm({ ...smtpForm, password: e.target.value })} />
                <Input placeholder="From email" value={smtpForm.from_email} onChange={(e) => setSmtpForm({ ...smtpForm, from_email: e.target.value })} />
                <Button onClick={() => saveSmtp(smtpForm)}>Save configuration</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="logs" className="mt-4">
          <Card className="surface-card">
            <CardHeader><CardTitle className="flex items-center gap-2"><FileText className="h-5 w-5" /> Delivery logs</CardTitle></CardHeader>
            <CardContent className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="py-2 pr-4">Recipient</th>
                    <th className="py-2 pr-4">Event</th>
                    <th className="py-2 pr-4">Status</th>
                    <th className="py-2">Sent</th>
                  </tr>
                </thead>
                <tbody>
                  {(logs as { recipient: string; event_name: string; status: string; sent_at?: string }[]).map((l, i) => (
                    <tr key={i} className="border-b border-border/40">
                      <td className="py-2 pr-4">{l.recipient}</td>
                      <td className="py-2 pr-4 font-mono text-xs">{l.event_name}</td>
                      <td className="py-2 pr-4"><StatusBadge status={l.status} /></td>
                      <td className="py-2 text-muted-foreground text-xs">{l.sent_at || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="queue" className="mt-4">
          <Card className="surface-card">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Email queue</CardTitle>
              <Button size="sm" variant="outline" onClick={() => fetchQueue()}>
                Refresh
              </Button>
            </CardHeader>
            <CardContent className="space-y-2">
              {queue.map((q: EmailQueueRow) => {
                const stalled =
                  q.status === 'processing' &&
                  (!q.created_at || Date.parse(q.created_at) < Date.now() - 5 * 60 * 1000);
                return (
                  <div
                    key={q.id}
                    className="flex flex-wrap items-center justify-between gap-2 rounded-lg border p-3 text-sm"
                  >
                    <span>{q.recipient}</span>
                    <span className="font-mono text-xs text-muted-foreground">{q.event_name}</span>
                    <StatusBadge status={q.status} />
                    <span className="text-xs">retries: {q.retry_count}</span>
                    {(stalled || q.status === 'retry' || q.status === 'dead_letter') && (
                      <Button size="sm" variant="outline" onClick={() => retryQueueItem(q.id)}>
                        Retry
                      </Button>
                    )}
                  </div>
                );
              })}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="mt-4">
          <Card className="surface-card">
            <CardHeader><CardTitle className="flex items-center gap-2"><BarChart3 className="h-5 w-5" /> Analytics</CardTitle></CardHeader>
            <CardContent>
              <pre className="text-xs bg-muted/30 rounded-lg p-4 overflow-auto">{JSON.stringify(analytics, null, 2)}</pre>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const variant =
    status === 'active' || status === 'sent' ? 'default' :
    status === 'failed' || status === 'dead_letter' ? 'destructive' :
    'secondary';
  return <Badge variant={variant as 'default' | 'destructive' | 'secondary'}>{status}</Badge>;
}

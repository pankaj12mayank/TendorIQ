'use client';

import { useCallback, useState } from 'react';
import { api } from '@/lib/api-client';
import { toast } from 'sonner';

export interface EmailTemplate {
  id: string;
  slug: string;
  name: string;
  subject: string;
  html_body: string;
  text_body?: string;
  variables: string[];
  variable_defaults: Record<string, unknown>;
  status: 'active' | 'inactive' | 'archived';
  version: number;
  sender_name?: string;
  reply_to?: string;
  branding?: Record<string, unknown>;
}

export interface EmailEventRow {
  event_key: string;
  name: string;
  category: string;
  description: string;
  default_template_slug: string;
  required_variables: string[];
  is_enabled: boolean;
  template_id?: string;
  id?: string;
}

export interface EmailAnalytics {
  period_days: number;
  total: number;
  sent: number;
  failed: number;
  delivery_rate: number;
  failure_rate: number;
  open_rate: number;
  click_rate: number;
  queue_pending: number;
  queue_processing: number;
  by_status: Record<string, number>;
  by_event: Record<string, number>;
}

export interface EmailQueueRow {
  id: string;
  recipient: string;
  event_name: string;
  status: string;
  retry_count: number;
  max_retries: number;
  next_retry_at?: string | null;
  error_message?: string | null;
  created_at?: string | null;
}

export function useEmailSystem() {
  const [loading, setLoading] = useState(false);
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [events, setEvents] = useState<EmailEventRow[]>([]);
  const [analytics, setAnalytics] = useState<EmailAnalytics | null>(null);
  const [logs, setLogs] = useState<unknown[]>([]);
  const [queue, setQueue] = useState<EmailQueueRow[]>([]);
  const [smtpConfigs, setSmtpConfigs] = useState<unknown[]>([]);

  const withLoading = useCallback(async <T>(fn: () => Promise<T>): Promise<T> => {
    setLoading(true);
    try {
      return await fn();
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchTemplates = useCallback(async () => {
    const data = await withLoading(() =>
      api.get<EmailTemplate[]>('/api/v1/email/templates?include_archived=true')
    );
    setTemplates(data);
  }, [withLoading]);

  const fetchEvents = useCallback(async () => {
    const data = await withLoading(() => api.get<EmailEventRow[]>('/api/v1/email/events'));
    setEvents(data);
  }, [withLoading]);

  const fetchAnalytics = useCallback(async () => {
    const data = await withLoading(() => api.get<EmailAnalytics>('/api/v1/email/analytics'));
    setAnalytics(data);
  }, [withLoading]);

  const fetchLogs = useCallback(async () => {
    const data = await withLoading(() => api.get<unknown[]>('/api/v1/email/logs'));
    setLogs(data);
  }, [withLoading]);

  const fetchQueue = useCallback(async () => {
    const data = await withLoading(() => api.get<EmailQueueRow[]>('/api/v1/email/queue'));
    setQueue(data);
  }, [withLoading]);

  const fetchSmtp = useCallback(async () => {
    const data = await withLoading(() => api.get<unknown[]>('/api/v1/email/settings/smtp'));
    setSmtpConfigs(data);
  }, [withLoading]);

  const createTemplate = useCallback(
    async (body: Partial<EmailTemplate>) => {
      await withLoading(() =>
        api.post('/api/v1/email/templates', { status: 'inactive', variables: [], ...body })
      );
      toast.success('Template created');
      await fetchTemplates();
    },
    [withLoading, fetchTemplates]
  );

  const updateTemplate = useCallback(
    async (id: string, body: Partial<EmailTemplate>) => {
      await withLoading(() => api.patch(`/api/v1/email/templates/${id}`, body));
      toast.success('Template saved');
      await fetchTemplates();
    },
    [withLoading, fetchTemplates]
  );

  const activateTemplate = useCallback(
    async (id: string) => {
      await withLoading(() => api.post(`/api/v1/email/templates/${id}/activate`, {}));
      toast.success('Template activated');
      await fetchTemplates();
    },
    [withLoading, fetchTemplates]
  );

  const deactivateTemplate = useCallback(
    async (id: string) => {
      await withLoading(() => api.post(`/api/v1/email/templates/${id}/deactivate`, {}));
      toast.success('Template deactivated');
      await fetchTemplates();
    },
    [withLoading, fetchTemplates]
  );

  const archiveTemplate = useCallback(
    async (id: string) => {
      await withLoading(() => api.delete(`/api/v1/email/templates/${id}`));
      toast.success('Template archived (not deleted)');
      await fetchTemplates();
    },
    [withLoading, fetchTemplates]
  );

  const duplicateTemplate = useCallback(
    async (id: string) => {
      await withLoading(() => api.post(`/api/v1/email/templates/${id}/duplicate`, {}));
      toast.success('Template duplicated');
      await fetchTemplates();
    },
    [withLoading, fetchTemplates]
  );

  const testSend = useCallback(
    async (to: string, templateId: string, variables: Record<string, unknown>) => {
      await withLoading(() =>
        api.post('/api/v1/email/test-send', { to, template_id: templateId, variables })
      );
      toast.success('Test email queued');
    },
    [withLoading]
  );

  const previewTemplate = useCallback(
    async (subject: string, html_body: string, variables: Record<string, unknown>) => {
      return withLoading(() =>
        api.post<{ subject: string; html: string; missing_variables: string[] }>(
          '/api/v1/email/templates/preview',
          { subject, html_body, variables }
        )
      );
    },
    [withLoading]
  );

  const updateEvent = useCallback(
    async (eventKey: string, data: { template_id?: string; is_enabled?: boolean }) => {
      await withLoading(() => api.patch(`/api/v1/email/events/${encodeURIComponent(eventKey)}`, data));
      toast.success('Event updated');
      await fetchEvents();
    },
    [withLoading, fetchEvents]
  );

  const saveSmtp = useCallback(
    async (data: Record<string, unknown>) => {
      await withLoading(() => api.post('/api/v1/email/settings/smtp', data));
      toast.success('SMTP configuration saved');
      await fetchSmtp();
    },
    [withLoading, fetchSmtp]
  );

  const testSmtp = useCallback(
    async (configId: string) => {
      const res = await withLoading(() =>
        api.post<{ success: boolean; error?: string }>(
          `/api/v1/email/settings/smtp/${configId}/test`,
          {}
        )
      );
      if (res.success) toast.success('SMTP connection OK');
      else toast.error(res.error || 'SMTP test failed');
    },
    [withLoading]
  );

  const retryQueueItem = useCallback(
    async (itemId: string) => {
      await withLoading(() => api.post(`/api/v1/email/queue/${itemId}/retry`, {}));
      toast.success('Queue item requeued');
      await fetchQueue();
      await fetchAnalytics();
    },
    [withLoading, fetchQueue, fetchAnalytics]
  );

  return {
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
  };
}

export async function requestPasswordReset(email: string) {
  return api.post('/api/v1/email/auth/forgot-password', { email });
}

export async function resetPassword(token: string, new_password: string) {
  return api.post('/api/v1/email/auth/reset-password', { token, new_password });
}

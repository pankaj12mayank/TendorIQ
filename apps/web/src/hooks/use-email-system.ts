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

function useEmailApi() {
  const [loading, setLoading] = useState(false);

  const request = useCallback(async <T>(path: string, options?: RequestInit): Promise<T> => {
    setLoading(true);
    try {
      const method = options?.method || 'GET';
      if (method === 'GET') return await api.get<T>(path);
      if (method === 'POST') return await api.post<T>(path, options?.body ? JSON.parse(options.body as string) : undefined);
      if (method === 'PATCH') return await api.patch<T>(path, options?.body ? JSON.parse(options.body as string) : undefined);
      if (method === 'PUT') return await api.put<T>(path, options?.body ? JSON.parse(options.body as string) : undefined);
      if (method === 'DELETE') return await api.delete<T>(path);
      throw new Error('Unsupported method');
    } finally {
      setLoading(false);
    }
  }, []);

  return { request, loading };
}

export function useEmailSystem() {
  const { request, loading } = useEmailApi();
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [events, setEvents] = useState<EmailEventRow[]>([]);
  const [analytics, setAnalytics] = useState<EmailAnalytics | null>(null);
  const [logs, setLogs] = useState<unknown[]>([]);
  const [queue, setQueue] = useState<unknown[]>([]);
  const [smtpConfigs, setSmtpConfigs] = useState<unknown[]>([]);

  const fetchTemplates = useCallback(async () => {
    const data = await request<EmailTemplate[]>('/api/v1/email/templates?include_archived=true');
    setTemplates(data);
  }, [request]);

  const fetchEvents = useCallback(async () => {
    const data = await request<EmailEventRow[]>('/api/v1/email/events');
    setEvents(data);
  }, [request]);

  const fetchAnalytics = useCallback(async () => {
    const data = await request<EmailAnalytics>('/api/v1/email/analytics');
    setAnalytics(data);
  }, [request]);

  const fetchLogs = useCallback(async () => {
    const data = await request<unknown[]>('/api/v1/email/logs');
    setLogs(data);
  }, [request]);

  const fetchQueue = useCallback(async () => {
    const data = await request<unknown[]>('/api/v1/email/queue');
    setQueue(data);
  }, [request]);

  const fetchSmtp = useCallback(async () => {
    const data = await request<unknown[]>('/api/v1/email/settings/smtp');
    setSmtpConfigs(data);
  }, [request]);

  const createTemplate = useCallback(
    async (body: Partial<EmailTemplate>) => {
      await request('/api/v1/email/templates', {
        method: 'POST',
        body: JSON.stringify({ status: 'inactive', variables: [], ...body }),
      });
      toast.success('Template created');
      await fetchTemplates();
    },
    [request, fetchTemplates]
  );

  const updateTemplate = useCallback(
    async (id: string, body: Partial<EmailTemplate>) => {
      await request(`/api/v1/email/templates/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(body),
      });
      toast.success('Template saved');
      await fetchTemplates();
    },
    [request, fetchTemplates]
  );

  const activateTemplate = useCallback(
    async (id: string) => {
      await request(`/api/v1/email/templates/${id}/activate`, { method: 'POST', body: '{}' });
      toast.success('Template activated');
      await fetchTemplates();
    },
    [request, fetchTemplates]
  );

  const deactivateTemplate = useCallback(
    async (id: string) => {
      await request(`/api/v1/email/templates/${id}/deactivate`, { method: 'POST', body: '{}' });
      toast.success('Template deactivated');
      await fetchTemplates();
    },
    [request, fetchTemplates]
  );

  const archiveTemplate = useCallback(
    async (id: string) => {
      await request(`/api/v1/email/templates/${id}`, { method: 'DELETE' });
      toast.success('Template archived (not deleted)');
      await fetchTemplates();
    },
    [request, fetchTemplates]
  );

  const duplicateTemplate = useCallback(
    async (id: string) => {
      await request(`/api/v1/email/templates/${id}/duplicate`, { method: 'POST', body: '{}' });
      toast.success('Template duplicated');
      await fetchTemplates();
    },
    [request, fetchTemplates]
  );

  const testSend = useCallback(
    async (to: string, templateId: string, variables: Record<string, unknown>) => {
      await request('/api/v1/email/test-send', {
        method: 'POST',
        body: JSON.stringify({ to, template_id: templateId, variables }),
      });
      toast.success('Test email queued');
    },
    [request]
  );

  const previewTemplate = useCallback(
    async (subject: string, html_body: string, variables: Record<string, unknown>) => {
      return request<{ subject: string; html: string; missing_variables: string[] }>(
        '/api/v1/email/templates/preview',
        { method: 'POST', body: JSON.stringify({ subject, html_body, variables }) }
      );
    },
    [request]
  );

  const updateEvent = useCallback(
    async (eventKey: string, data: { template_id?: string; is_enabled?: boolean }) => {
      await request(`/api/v1/email/events/${encodeURIComponent(eventKey)}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      });
      toast.success('Event updated');
      await fetchEvents();
    },
    [request, fetchEvents]
  );

  const saveSmtp = useCallback(
    async (data: Record<string, unknown>) => {
      await request('/api/v1/email/settings/smtp', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      toast.success('SMTP configuration saved');
      await fetchSmtp();
    },
    [request, fetchSmtp]
  );

  const testSmtp = useCallback(
    async (configId: string) => {
      const res = await request<{ success: boolean; error?: string }>(
        `/api/v1/email/settings/smtp/${configId}/test`,
        { method: 'POST', body: '{}' }
      );
      if (res.success) toast.success('SMTP connection OK');
      else toast.error(res.error || 'SMTP test failed');
    },
    [request]
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
  };
}

export async function requestPasswordReset(email: string) {
  return api.post('/api/v1/email/auth/forgot-password', { email });
}

export async function resetPassword(token: string, new_password: string) {
  return api.post('/api/v1/email/auth/reset-password', { token, new_password });
}

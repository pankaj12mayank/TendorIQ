import { useCallback, useState } from 'react';
import { toast } from 'sonner';

import {
  PLATFORM_AUDIT_EXPORT_MAX_ROWS,
  PLATFORM_AUDIT_LIST_LIMIT,
} from '@/lib/audit-constants';
import { api } from '@/lib/api-client';
import { ADMIN_PLATFORM_PATHS } from '@/lib/admin-platform-paths';
import { parsePlatformAuditLogsResponse } from '@/lib/admin-platform-api';
import { AuditLogEntry, AdvancedFilter } from '@/components/admin/types';

import { reportAdminApiError } from './admin-api-errors';

export function useAuditLogApi() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [isLoading, setLoading] = useState(false);

  const fetchLogs = useCallback(async (_filters?: AdvancedFilter[]) => {
    setLoading(true);
    try {
      const res = await api.get<unknown>(ADMIN_PLATFORM_PATHS.auditLogs, {
        params: { limit: PLATFORM_AUDIT_LIST_LIMIT },
      });
      setLogs(parsePlatformAuditLogsResponse(res));
    } catch (err) {
      reportAdminApiError(err, 'Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  }, []);

  const exportLogs = useCallback(async (format: 'csv' | 'json') => {
    setLoading(true);
    try {
      const res = await api.post<{ content: string | unknown; mime_type: string }>(
        ADMIN_PLATFORM_PATHS.auditLogsExport,
        { format, limit: PLATFORM_AUDIT_EXPORT_MAX_ROWS }
      );
      const body =
        typeof res.content === 'string' ? res.content : JSON.stringify(res.content, null, 2);
      const mime = res.mime_type || (format === 'csv' ? 'text/csv' : 'application/json');
      const blob = new Blob([body], { type: mime });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `platform-audit-logs.${format}`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success('Platform audit export downloaded');
    } catch (err) {
      reportAdminApiError(err, 'Export failed');
    } finally {
      setLoading(false);
    }
  }, []);

  const getLogById = useCallback((id: string) => logs.find((l) => l.id === id), [logs]);

  return { logs, isLoading, fetchLogs, exportLogs, getLogById };
}

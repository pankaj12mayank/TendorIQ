import { useCallback, useState } from 'react';
import { toast } from 'sonner';

import { api } from '@/lib/api-client';
import { ADMIN_PLATFORM_PATHS } from '@/lib/admin-platform-paths';
import { parsePlatformFailedJobsResponse } from '@/lib/admin-platform-api';
import { FailedJob } from '@/components/admin/types';

import { reportAdminApiError } from './admin-api-errors';

export function useFailedJobsApi() {
  const [jobs, setJobs] = useState<FailedJob[]>([]);
  const [isLoading, setLoading] = useState(false);

  const fetchFailedJobs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get<unknown>(ADMIN_PLATFORM_PATHS.failedJobs);
      setJobs(parsePlatformFailedJobsResponse(res));
    } catch (err) {
      reportAdminApiError(err, 'Failed to load failed jobs');
    } finally {
      setLoading(false);
    }
  }, []);

  const retryJob = useCallback(async (id: string) => {
    try {
      await api.post(ADMIN_PLATFORM_PATHS.queueJobRetry(id));
      await api.delete(ADMIN_PLATFORM_PATHS.failedJob(id));
      setJobs((prev) => prev.filter((j) => j.id !== id));
      toast.success('Job retry scheduled');
    } catch (err) {
      reportAdminApiError(err, 'Retry failed');
    }
  }, []);

  const retryAll = useCallback(async () => {
    const retryable = jobs.filter((j) => j.retryable);
    await Promise.allSettled(retryable.map((j) => retryJob(j.id)));
  }, [jobs, retryJob]);

  const deleteJob = useCallback(async (id: string) => {
    try {
      await api.delete(ADMIN_PLATFORM_PATHS.failedJob(id));
      setJobs((prev) => prev.filter((j) => j.id !== id));
      toast.success('Failed job dismissed');
    } catch (err) {
      reportAdminApiError(err, 'Unable to remove job');
    }
  }, []);

  const clearAll = useCallback(async () => {
    await Promise.allSettled(jobs.map((j) => api.delete(ADMIN_PLATFORM_PATHS.failedJob(j.id))));
    setJobs([]);
    toast.success('Failed jobs cleared');
  }, [jobs]);

  return {
    jobs,
    isLoading,
    fetchFailedJobs,
    retryJob,
    retryAll,
    deleteJob,
    clearAll,
  };
}

import { useCallback, useState } from 'react';
import { toast } from 'sonner';

import { api } from '@/lib/api-client';
import { ADMIN_PLATFORM_PATHS } from '@/lib/admin-platform-paths';
import { parsePlatformQueueJobsResponse } from '@/lib/admin-platform-api';
import { QueueJob } from '@/components/admin/types';

import { reportAdminApiError } from './admin-api-errors';

export function useQueueApi() {
  const [jobs, setJobs] = useState<QueueJob[]>([]);
  const [isLoading, setLoading] = useState(false);

  const refreshJobs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get<unknown>(ADMIN_PLATFORM_PATHS.queueJobs);
      setJobs(parsePlatformQueueJobsResponse(res));
    } catch (err) {
      reportAdminApiError(err, 'Failed to load queue');
    } finally {
      setLoading(false);
    }
  }, []);

  const retryJob = useCallback(
    async (id: string) => {
      try {
        await api.post(ADMIN_PLATFORM_PATHS.queueJobRetry(id));
        toast.success('Job retry scheduled');
        await refreshJobs();
      } catch (err) {
        reportAdminApiError(err, 'Retry failed');
      }
    },
    [refreshJobs]
  );

  const cancelJob = useCallback(
    async (id: string) => {
      try {
        await api.post(ADMIN_PLATFORM_PATHS.queueJobCancel(id));
        toast.success('Job cancelled');
        await refreshJobs();
      } catch (err) {
        reportAdminApiError(err, 'Failed to cancel job');
      }
    },
    [refreshJobs]
  );

  const pauseJob = useCallback(
    async (id: string) => {
      try {
        await api.post(ADMIN_PLATFORM_PATHS.queueJobPause(id));
        toast.success('Job paused');
        await refreshJobs();
      } catch (err) {
        reportAdminApiError(err, 'Failed to pause job');
      }
    },
    [refreshJobs]
  );

  const resumeJob = useCallback(
    async (id: string) => {
      try {
        await api.post(ADMIN_PLATFORM_PATHS.queueJobResume(id));
        toast.success('Job resumed');
        await refreshJobs();
      } catch (err) {
        reportAdminApiError(err, 'Failed to resume job');
      }
    },
    [refreshJobs]
  );

  return { jobs, isLoading, refreshJobs, retryJob, cancelJob, pauseJob, resumeJob };
}

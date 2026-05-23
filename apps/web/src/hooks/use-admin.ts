/**
 * Super-admin platform hooks — split by domain under `@/hooks/admin/*`.
 * Import from here or from `@/hooks/admin` directly.
 */
export {
  useAdminUsersApi,
  useAdminBillingApi,
  useBillingApi,
  useAIProvidersApi,
  usePromptsApi,
  useQueueApi,
  useAuditLogApi,
  useFailedJobsApi,
} from './admin';

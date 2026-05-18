import { useCallback, useState } from 'react';
import { useAdminStore } from '@/components/admin/store';
import { 
  User, 
  UserRole, 
  BillingPlan, 
  AIProvider, 
  PromptTemplate,
  QueueJob,
  AuditLogEntry,
  FailedJob,
  AdminModule,
  AdvancedFilter,
  PaginationState,
  SortState
} from '@/components/admin/types';
import { 
  MOCK_USERS, 
  MOCK_BILLING_PLANS, 
  MOCK_AI_PROVIDERS, 
  MOCK_PROMPTS,
  MOCK_QUEUE_JOBS,
  MOCK_AUDIT_LOGS,
  MOCK_FAILED_JOBS
} from '@/components/admin/constants';

interface UseAdminApiReturn {
  users: User[];
  isLoading: boolean;
  isError: boolean;
  error: string | null;
  fetchUsers: (filters?: AdvancedFilter[]) => Promise<void>;
  createUser: (user: Partial<User>) => Promise<void>;
  updateUser: (id: string, data: Partial<User>) => Promise<void>;
  deleteUser: (id: string) => Promise<void>;
  updateUserRole: (id: string, role: UserRole) => Promise<void>;
  toggleUserStatus: (id: string) => Promise<void>;
}

export function useAdminUsersApi(): UseAdminApiReturn {
  const { users, setUsers, isLoading, setLoading } = useAdminStore();
  const [isError, setIsError] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchUsers = useCallback(async (filters?: AdvancedFilter[]) => {
    setIsError(false);
    setError(null);
    setLoading(true);

    try {
      await new Promise(resolve => setTimeout(resolve, 800));
      
      let filteredUsers = [...MOCK_USERS];
      
      if (filters) {
        filters.forEach(filter => {
          filteredUsers = filteredUsers.filter(user => {
            const value = (user as Record<string, unknown>)[filter.field];
            switch (filter.operator) {
              case 'eq':
                return value === filter.value;
              case 'ne':
                return value !== filter.value;
              case 'contains':
                return String(value).toLowerCase().includes(String(filter.value).toLowerCase());
              case 'in':
                return (filter.value as string[]).includes(String(value));
              default:
                return true;
            }
          });
        });
      }
      
      setUsers(filteredUsers);
    } catch (err) {
      setIsError(true);
      setError('Failed to fetch users');
    } finally {
      setLoading(false);
    }
  }, [setUsers, setLoading]);

  const createUser = useCallback(async (userData: Partial<User>) => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    
    const newUser: User = {
      id: `user-${Date.now()}`,
      name: userData.name || 'New User',
      email: userData.email || 'new@example.com',
      role: userData.role || 'viewer',
      status: 'pending',
      organization: userData.organization || 'Organization',
      lastActive: new Date().toISOString(),
      createdAt: new Date().toISOString(),
      permissions: userData.permissions || ['read'],
    };
    
    useAdminStore.getState().addUser(newUser);
    setLoading(false);
  }, [setLoading]);

  const updateUser = useCallback(async (id: string, data: Partial<User>) => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    useAdminStore.getState().updateUser(id, data);
    setLoading(false);
  }, [setLoading]);

  const deleteUser = useCallback(async (id: string) => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    useAdminStore.getState().deleteUser(id);
    setLoading(false);
  }, [setLoading]);

  const updateUserRole = useCallback(async (id: string, role: UserRole) => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    useAdminStore.getState().updateUser(id, { role });
    setLoading(false);
  }, [setLoading]);

  const toggleUserStatus = useCallback(async (id: string) => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    const user = useAdminStore.getState().users.find(u => u.id === id);
    if (user) {
      const newStatus = user.status === 'active' ? 'inactive' : 'active';
      useAdminStore.getState().updateUser(id, { status: newStatus });
    }
    setLoading(false);
  }, [setLoading]);

  return {
    users,
    isLoading,
    isError,
    error,
    fetchUsers,
    createUser,
    updateUser,
    deleteUser,
    updateUserRole,
    toggleUserStatus,
  };
}

interface UseBillingApiReturn {
  plans: BillingPlan[];
  isLoading: boolean;
  createPlan: (plan: Partial<BillingPlan>) => Promise<void>;
  updatePlan: (id: string, data: Partial<BillingPlan>) => Promise<void>;
  deletePlan: (id: string) => Promise<void>;
}

export function useBillingApi(): UseBillingApiReturn {
  const [plans, setPlans] = useState<BillingPlan[]>(MOCK_BILLING_PLANS);
  const [isLoading, setLoading] = useState(false);

  const createPlan = useCallback(async (planData: Partial<BillingPlan>) => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    const newPlan: BillingPlan = {
      id: `plan-${Date.now()}`,
      name: planData.name || 'New Plan',
      price: planData.price || 0,
      interval: planData.interval || 'monthly',
      features: planData.features || [],
      limits: planData.limits || { users: 0, documents: 0, apiCalls: 0, storage: 0 },
    };
    setPlans([...plans, newPlan]);
    setLoading(false);
  }, [plans]);

  const updatePlan = useCallback(async (id: string, data: Partial<BillingPlan>) => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    setPlans(plans.map(p => p.id === id ? { ...p, ...data } : p));
    setLoading(false);
  }, [plans]);

  const deletePlan = useCallback(async (id: string) => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    setPlans(plans.filter(p => p.id !== id));
    setLoading(false);
  }, [plans]);

  return { plans, isLoading, createPlan, updatePlan, deletePlan };
}

interface UseAIProvidersApiReturn {
  providers: AIProvider[];
  isLoading: boolean;
  addProvider: (provider: Partial<AIProvider>) => Promise<void>;
  updateProvider: (id: string, data: Partial<AIProvider>) => Promise<void>;
  deleteProvider: (id: string) => Promise<void>;
  toggleProvider: (id: string) => Promise<void>;
  updateSettings: (providerId: string, settings: AIProvider['settings']) => Promise<void>;
}

export function useAIProvidersApi(): UseAIProvidersApiReturn {
  const [providers, setProviders] = useState<AIProvider[]>(MOCK_AI_PROVIDERS);
  const [isLoading, setLoading] = useState(false);

  const addProvider = useCallback(async (providerData: Partial<AIProvider>) => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    const newProvider: AIProvider = {
      id: `provider-${Date.now()}`,
      name: providerData.name || 'New Provider',
      type: providerData.type || 'openai',
      apiKeyMasked: 'sk-****-xxxx',
      isActive: true,
      models: providerData.models || [],
      settings: providerData.settings || { temperature: 0.7, maxTokens: 2048, topP: 1, frequencyPenalty: 0, presencePenalty: 0 },
    };
    setProviders([...providers, newProvider]);
    setLoading(false);
  }, [providers]);

  const updateProvider = useCallback(async (id: string, data: Partial<AIProvider>) => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    setProviders(providers.map(p => p.id === id ? { ...p, ...data } : p));
    setLoading(false);
  }, [providers]);

  const deleteProvider = useCallback(async (id: string) => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    setProviders(providers.filter(p => p.id !== id));
    setLoading(false);
  }, [providers]);

  const toggleProvider = useCallback(async (id: string) => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 300));
    setProviders(providers.map(p => p.id === id ? { ...p, isActive: !p.isActive } : p));
    setLoading(false);
  }, [providers]);

  const updateSettings = useCallback(async (providerId: string, settings: AIProvider['settings']) => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    setProviders(providers.map(p => p.id === providerId ? { ...p, settings } : p));
    setLoading(false);
  }, [providers]);

  return { providers, isLoading, addProvider, updateProvider, deleteProvider, toggleProvider, updateSettings };
}

interface UsePromptsApiReturn {
  prompts: PromptTemplate[];
  isLoading: boolean;
  createPrompt: (prompt: Partial<PromptTemplate>) => Promise<void>;
  updatePrompt: (id: string, data: Partial<PromptTemplate>) => Promise<void>;
  deletePrompt: (id: string) => Promise<void>;
  togglePromptActive: (id: string) => Promise<void>;
  testPrompt: (id: string, variables: Record<string, unknown>) => Promise<string>;
}

export function usePromptsApi(): UsePromptsApiReturn {
  const [prompts, setPrompts] = useState<PromptTemplate[]>(MOCK_PROMPTS);
  const [isLoading, setLoading] = useState(false);

  const createPrompt = useCallback(async (promptData: Partial<PromptTemplate>) => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    const newPrompt: PromptTemplate = {
      id: `prompt-${Date.now()}`,
      name: promptData.name || 'New Prompt',
      description: promptData.description || '',
      category: promptData.category || 'custom',
      content: promptData.content || '',
      variables: promptData.variables || [],
      version: 1,
      isActive: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      createdBy: 'Admin',
    };
    setPrompts([...prompts, newPrompt]);
    setLoading(false);
  }, [prompts]);

  const updatePrompt = useCallback(async (id: string, data: Partial<PromptTemplate>) => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    setPrompts(prompts.map(p => p.id === id ? { ...p, ...data, updatedAt: new Date().toISOString() } : p));
    setLoading(false);
  }, [prompts]);

  const deletePrompt = useCallback(async (id: string) => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    setPrompts(prompts.filter(p => p.id !== id));
    setLoading(false);
  }, [prompts]);

  const togglePromptActive = useCallback(async (id: string) => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 300));
    setPrompts(prompts.map(p => p.id === id ? { ...p, isActive: !p.isActive } : p));
    setLoading(false);
  }, [prompts]);

  const testPrompt = useCallback(async (id: string, variables: Record<string, unknown>): Promise<string> => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 2000));
    const prompt = prompts.find(p => p.id === id);
    let result = prompt?.content || '';
    Object.entries(variables).forEach(([key, value]) => {
      result = result.replace(`{${key}}`, String(value));
    });
    setLoading(false);
    return result;
  }, [prompts]);

  return { prompts, isLoading, createPrompt, updatePrompt, deletePrompt, togglePromptActive, testPrompt };
}

interface UseQueueApiReturn {
  jobs: QueueJob[];
  isLoading: boolean;
  refreshJobs: () => Promise<void>;
  retryJob: (id: string) => Promise<void>;
  cancelJob: (id: string) => Promise<void>;
  pauseJob: (id: string) => Promise<void>;
  resumeJob: (id: string) => Promise<void>;
}

export function useQueueApi(): UseQueueApiReturn {
  const [jobs, setJobs] = useState<QueueJob[]>(MOCK_QUEUE_JOBS);
  const [isLoading, setLoading] = useState(false);

  const refreshJobs = useCallback(async () => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    setJobs([...jobs]);
    setLoading(false);
  }, [jobs]);

  const retryJob = useCallback(async (id: string) => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    setJobs(jobs.map(j => j.id === id ? { ...j, status: 'pending' as const, attempts: 0, error: undefined } : j));
    setLoading(false);
  }, [jobs]);

  const cancelJob = useCallback(async (id: string) => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    setJobs(jobs.filter(j => j.id !== id));
    setLoading(false);
  }, [jobs]);

  const pauseJob = useCallback(async (id: string) => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 300));
    setJobs(jobs.map(j => j.id === id ? { ...j, status: 'pending' as const } : j));
    setLoading(false);
  }, [jobs]);

  const resumeJob = useCallback(async (id: string) => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 300));
    setJobs(jobs.map(j => j.id === id ? { ...j, status: 'processing' as const } : j));
    setLoading(false);
  }, [jobs]);

  return { jobs, isLoading, refreshJobs, retryJob, cancelJob, pauseJob, resumeJob };
}

interface UseAuditLogApiReturn {
  logs: AuditLogEntry[];
  isLoading: boolean;
  fetchLogs: (filters?: AdvancedFilter[]) => Promise<void>;
  exportLogs: (format: 'csv' | 'json' | 'pdf') => Promise<void>;
  getLogById: (id: string) => AuditLogEntry | undefined;
}

export function useAuditLogApi(): UseAuditLogApiReturn {
  const [logs, setLogs] = useState<AuditLogEntry[]>(MOCK_AUDIT_LOGS);
  const [isLoading, setLoading] = useState(false);

  const fetchLogs = useCallback(async (filters?: AdvancedFilter[]) => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 800));
    
    let filteredLogs = [...MOCK_AUDIT_LOGS];
    
    if (filters) {
      filters.forEach(filter => {
        filteredLogs = filteredLogs.filter(log => {
          const value = (log as Record<string, unknown>)[filter.field];
          switch (filter.operator) {
            case 'contains':
              return String(value).toLowerCase().includes(String(filter.value).toLowerCase());
            case 'eq':
              return value === filter.value;
            default:
              return true;
          }
        });
      });
    }
    
    setLogs(filteredLogs);
    setLoading(false);
  }, []);

  const exportLogs = useCallback(async (format: 'csv' | 'json' | 'pdf') => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    const data = format === 'json' ? JSON.stringify(logs, null, 2) : JSON.stringify(logs);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-logs.${format}`;
    a.click();
    URL.revokeObjectURL(url);
    
    setLoading(false);
  }, [logs]);

  const getLogById = useCallback((id: string) => {
    return logs.find(l => l.id === id);
  }, [logs]);

  return { logs, isLoading, fetchLogs, exportLogs, getLogById };
}

interface UseFailedJobsApiReturn {
  jobs: FailedJob[];
  isLoading: boolean;
  retryJob: (id: string) => Promise<void>;
  retryAll: () => Promise<void>;
  deleteJob: (id: string) => Promise<void>;
  clearAll: () => Promise<void>;
}

export function useFailedJobsApi(): UseFailedJobsApiReturn {
  const [jobs, setJobs] = useState<FailedJob[]>(MOCK_FAILED_JOBS);
  const [isLoading, setLoading] = useState(false);

  const retryJob = useCallback(async (id: string) => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    setJobs(jobs.filter(j => j.id !== id));
    setLoading(false);
  }, [jobs]);

  const retryAll = useCallback(async () => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 2000));
    setJobs(jobs.filter(j => !j.retryable));
    setLoading(false);
  }, [jobs]);

  const deleteJob = useCallback(async (id: string) => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    setJobs(jobs.filter(j => j.id !== id));
    setLoading(false);
  }, [jobs]);

  const clearAll = useCallback(async () => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    setJobs([]);
    setLoading(false);
  }, []);

  return { jobs, isLoading, retryJob, retryAll, deleteJob, clearAll };
}
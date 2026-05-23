'use client';

import { useCallback, useState } from 'react';
import { api } from '@/lib/api-client';
import { parseSsoTenantConfig, type SsoPublicConfig, type SsoTenantConfig } from '@/lib/sso-api';
import {
  exchangeSsoSession,
  fetchPublicSsoConfig,
  fetchPublicSsoLoginUrl,
} from '@/lib/sso-session';
import { setStoredSession } from '@/lib/auth-session';
import type { AuthUser } from '@/lib/auth-session';

export function useSsoSignIn(orgSlug: string | null) {
  const [publicConfig, setPublicConfig] = useState<SsoPublicConfig | null>(null);
  const [isLoading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadPublicConfig = useCallback(async (slug: string) => {
    setLoading(true);
    setError(null);
    try {
      const config = await fetchPublicSsoConfig(slug);
      setPublicConfig(config);
      return config;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load SSO config');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const signInWithToken = useCallback(async (slug: string, token: string) => {
    setLoading(true);
    setError(null);
    try {
      const exchanged = await exchangeSsoSession(slug, token);
      if (!exchanged) {
        setError('SSO sign-in failed');
        return null;
      }
      setStoredSession(exchanged.token, exchanged.user, {
        refreshToken: exchanged.refreshToken,
        expiresInSec: exchanged.expiresIn,
      });
      return exchanged.user;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'SSO sign-in failed');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const resolveLoginUrl = useCallback(async (slug: string, redirectUri: string) => {
    return fetchPublicSsoLoginUrl(slug, redirectUri);
  }, []);

  return {
    orgSlug,
    publicConfig,
    isLoading,
    error,
    loadPublicConfig,
    signInWithToken,
    resolveLoginUrl,
  };
}

export function useSsoAdmin() {
  const [config, setConfig] = useState<SsoTenantConfig | null>(null);
  const [providers, setProviders] = useState<{ id: string; name: string }[]>([]);
  const [isLoading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchConfig = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<unknown>('/api/v1/sso/config');
      setConfig(parseSsoTenantConfig(res));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load SSO settings');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchProviders = useCallback(async () => {
    const res = await api.get<{ id: string; name: string }[]>('/api/v1/sso/providers');
    setProviders(Array.isArray(res) ? res : []);
    return res;
  }, []);

  const configure = useCallback(
    async (body: Record<string, unknown>) => {
      setLoading(true);
      setError(null);
      try {
        await api.post('/api/v1/sso/configure', body);
        await fetchConfig();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to save SSO settings');
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [fetchConfig]
  );

  const disable = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await api.post('/api/v1/sso/disable');
      await fetchConfig();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to disable SSO');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchConfig]);

  return {
    config,
    providers,
    isLoading,
    error,
    fetchConfig,
    fetchProviders,
    configure,
    disable,
  };
}

export type { AuthUser };

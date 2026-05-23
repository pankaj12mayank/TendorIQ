import {
  tokensFromLoginResponse,
  userFromLoginResponse,
  type ClerkSessionExchangeResult,
} from './auth-api';

import { apiUrl } from './api-config';
import { authenticatedFetch } from './api-fetch';

export async function fetchPublicSsoConfig(orgSlug: string) {
  const { parseSsoPublicConfig } = await import('./sso-api');
  const slug = orgSlug.trim().toLowerCase();
  if (!slug) return null;
  const res = await authenticatedFetch(
    `/api/v1/sso/public/config?org_slug=${encodeURIComponent(slug)}`,
    { auth: false }
  );
  if (!res.ok) return null;
  return parseSsoPublicConfig(await res.json());
}

export async function fetchPublicSsoLoginUrl(
  orgSlug: string,
  redirectUri: string
): Promise<string | null> {
  const params = new URLSearchParams({
    org_slug: orgSlug.trim().toLowerCase(),
    redirect_uri: redirectUri,
  });
  const res = await authenticatedFetch(`/api/v1/sso/public/login-url?${params}`, { auth: false });
  if (!res.ok) return null;
  const data = (await res.json()) as { url?: string };
  return data.url ?? null;
}

/** Exchange IdP token for TenderIQ JWT (org-scoped, public route). */
export async function exchangeSsoSession(
  orgSlug: string,
  token: string
): Promise<ClerkSessionExchangeResult | null> {
  const res = await authenticatedFetch('/api/v1/sso/session', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ org_slug: orgSlug.trim().toLowerCase(), token }),
    auth: false,
  });
  if (!res.ok) return null;
  const data = await res.json();
  if (!data.token && !data.access_token) return null;
  const tokens = tokensFromLoginResponse(data);
  const user = userFromLoginResponse(data);
  return {
    token: tokens.access_token,
    refreshToken: tokens.refresh_token,
    expiresIn: tokens.expires_in,
    user,
  };
}

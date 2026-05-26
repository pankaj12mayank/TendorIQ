import { apiUrl } from '@/lib/api-config';
import { buildApiAuthHeaders } from '@/lib/auth-user';
import type { AuthUser } from '@/lib/auth-session';
import { getRolePermissions } from '@/lib/permissions';

export interface ApiSessionPayload {
  access_token: string;
  refresh_token?: string;
  expires_in?: number;
}

export function mapUserFromApi(data: Record<string, unknown>): AuthUser {
  const perms = Array.isArray(data.permissions) ? (data.permissions as string[]) : [];
  const membershipRole =
    (data.membership_role as string | undefined) ?? (data.role as string | undefined);
  const role = (data.role as string | undefined) ?? membershipRole;
  const companyProfile = data.company_profile as AuthUser['companyProfile'] | undefined;
  return {
    id: (data.user_id as string | undefined) ?? (data.id as string),
    email: data.email as string,
    name: (data.name as string | undefined) ?? (data.email as string)?.split('@')[0] ?? 'User',
    role,
    membershipRole,
    tenantId: (data.tenant_id as string | undefined) ?? undefined,
    companyProfile,
    permissions:
      perms.length > 0
        ? perms
        : getRolePermissions(
            membershipRole && role !== 'super_admin' ? membershipRole : role
          ),
  };
}

export type FetchMeResult = {
  user: AuthUser | null;
  unauthorized: boolean;
  /** True when API is down, CORS blocked, or browser could not connect */
  networkError?: boolean;
};

export async function fetchMeFromApi(
  token: string,
  existingUser?: AuthUser | null
): Promise<FetchMeResult> {
  try {
    const res = await fetch(apiUrl('/auth/me'), {
      headers: {
        'Content-Type': 'application/json',
        ...buildApiAuthHeaders(token, existingUser ?? undefined),
      },
      signal: AbortSignal.timeout(15_000),
    });
    if (res.status === 401) {
      return { user: null, unauthorized: true };
    }
    if (!res.ok) {
      return { user: null, unauthorized: false };
    }
    const data = await res.json();
    return { user: mapUserFromApi(data as Record<string, unknown>), unauthorized: false };
  } catch {
    return { user: null, unauthorized: false, networkError: true };
  }
}

export async function refreshAccessToken(
  refreshToken: string
): Promise<ApiSessionPayload | null> {
  try {
    const res = await fetch(apiUrl('/auth/refresh'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
      signal: AbortSignal.timeout(15_000),
    });
    if (!res.ok) return null;
    const data = await res.json();
    if (!data.access_token) return null;
    return {
      access_token: data.access_token as string,
      refresh_token: (data.refresh_token as string | undefined) ?? refreshToken,
      expires_in: data.expires_in as number | undefined,
    };
  } catch {
    return null;
  }
}

export function tokensFromLoginResponse(data: {
  token?: string;
  access_token?: string;
  refresh_token?: string;
  expires_in?: number;
}): ApiSessionPayload {
  const access = data.access_token ?? data.token;
  if (!access) {
    throw new Error('Login response missing access token');
  }
  return {
    access_token: access,
    refresh_token: data.refresh_token,
    expires_in: data.expires_in,
  };
}

export function userFromLoginResponse(data: {
  user?: Record<string, unknown>;
}): AuthUser {
  if (!data.user) {
    throw new Error('Login response missing user');
  }
  return mapUserFromApi(data.user);
}

export interface ClerkSessionExchangeResult {
  token: string;
  refreshToken?: string;
  expiresIn?: number;
  user: AuthUser;
}

export interface SupabaseSessionExchangeResult {
  token: string;
  refreshToken?: string;
  expiresIn?: number;
  user: AuthUser;
}

/** Exchange Supabase access token for TenderIQ API JWT + user profile. */
export async function exchangeSupabaseSession(
  supabaseAccessToken: string
): Promise<SupabaseSessionExchangeResult | null> {
  const res = await fetch(apiUrl('/api/v1/auth/supabase/session'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${supabaseAccessToken}`,
    },
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

/** Exchange Clerk session token for TenderIQ local JWT + user profile. */
export async function exchangeClerkSession(
  clerkToken: string
): Promise<ClerkSessionExchangeResult | null> {
  const res = await fetch(apiUrl('/api/v1/auth/clerk/session'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${clerkToken}`,
    },
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

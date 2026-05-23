export interface SsoPublicConfig {
  enabled: boolean;
  provider: string;
  org_slug: string;
  domain?: string;
}

export interface SsoTenantConfig {
  provider: string;
  enabled: boolean;
  domain?: string;
  tenant_id?: string;
  client_id?: string;
}

export function parseSsoPublicConfig(payload: unknown): SsoPublicConfig {
  const body = (payload ?? {}) as Record<string, unknown>;
  return {
    enabled: Boolean(body.enabled),
    provider: String(body.provider ?? 'none'),
    org_slug: String(body.org_slug ?? ''),
    domain: body.domain as string | undefined,
  };
}

export function parseSsoTenantConfig(payload: unknown): SsoTenantConfig {
  const body = (payload ?? {}) as Record<string, unknown>;
  return {
    provider: String(body.provider ?? 'none'),
    enabled: Boolean(body.enabled),
    domain: body.domain as string | undefined,
    tenant_id: body.tenant_id as string | undefined,
    client_id: body.client_id as string | undefined,
  };
}

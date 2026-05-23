import { describe, expect, it } from 'vitest';

import { parseSsoPublicConfig, parseSsoTenantConfig } from '../sso-api';

describe('sso-api', () => {
  it('parses public SSO config', () => {
    const cfg = parseSsoPublicConfig({
      enabled: true,
      provider: 'okta',
      org_slug: 'acme',
      domain: 'acme',
    });
    expect(cfg.enabled).toBe(true);
    expect(cfg.provider).toBe('okta');
    expect(cfg.org_slug).toBe('acme');
  });

  it('parses tenant SSO config without secrets', () => {
    const cfg = parseSsoTenantConfig({
      provider: 'azure_ad',
      enabled: true,
      tenant_id: 'tid-1',
      client_id: 'cid',
    });
    expect(cfg.enabled).toBe(true);
    expect(cfg.tenant_id).toBe('tid-1');
    expect((cfg as { client_secret?: string }).client_secret).toBeUndefined();
  });
});

import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

import { describe, expect, it } from 'vitest';

import { apiUrl } from '../api-config';
import { ROUTES } from '../routes';

const here = dirname(fileURLToPath(import.meta.url));
const contractPath = join(here, '../../../../api/tests/contracts/fe_api_paths.json');

interface FeApiContract {
  paths: string[];
}

function loadContract(): FeApiContract {
  return JSON.parse(readFileSync(contractPath, 'utf-8')) as FeApiContract;
}

describe('FE ↔ API path contract', () => {
  it('contract file lists paths the web app relies on', () => {
    const contract = loadContract();
    expect(contract.paths.length).toBeGreaterThan(10);
    expect(contract.paths).toContain('/api/v1/tenders');
    expect(contract.paths).toContain('/api/v1/auth/me');
  });

  it('canonical dashboard routes are defined in routes.ts', () => {
    expect(ROUTES.signIn).toBe('/sign-in');
    expect(ROUTES.dashboard).toMatch(/dashboard/);
    expect(ROUTES.tenderReview).toContain('review');
  });

  it('apiUrl builds absolute URLs for contract paths', () => {
    const url = apiUrl('/api/v1/tenders');
    expect(url).toMatch(/\/api\/v1\/tenders$/);
  });
});

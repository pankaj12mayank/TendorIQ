import { parsePaginated, unwrapData } from './api-envelope';

export interface OrganizationRow {
  id: string;
  name: string;
  slug: string;
  description?: string;
  website?: string;
  created_at?: string;
}

export function parseOrganizationsList(payload: unknown): OrganizationRow[] {
  const page = parsePaginated<OrganizationRow>(payload as { data?: OrganizationRow[] });
  if (page.data.length) return page.data;
  const rows = unwrapData<OrganizationRow[]>(payload);
  return Array.isArray(rows) ? rows : [];
}

export function parseOrganization(payload: unknown): OrganizationRow | null {
  const row = unwrapData<OrganizationRow>(payload);
  if (row && typeof row === 'object' && 'id' in row) return row;
  return null;
}

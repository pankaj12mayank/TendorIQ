import type { Document } from '@/stores/document-store';
import { unwrapData } from '@/lib/api-envelope';

export interface DocumentListResponse {
  success: boolean;
  documents: Document[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export function unwrapDocumentPayload<T extends Document>(payload: {
  success?: boolean;
  document?: T;
}): T {
  if (payload.document) {
    return payload.document;
  }
  return unwrapData(payload) as T;
}

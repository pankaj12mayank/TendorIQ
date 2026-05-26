'use client';

import { useEffect, useState } from 'react';

import type { PublicSitePayload } from '@/lib/public-site';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export type PublicSiteContent = PublicSitePayload;

export function useSiteContent(initial?: PublicSiteContent | null) {
  const [content, setContent] = useState<PublicSiteContent | null>(initial ?? null);
  const [loading, setLoading] = useState(!initial);

  useEffect(() => {
    if (initial) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/public/site`, { cache: 'no-store' });
        if (!res.ok) return;
        const json = await res.json();
        if (!cancelled) setContent(json.data ?? null);
      } catch {
        /* static fallbacks in sections */
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [initial]);

  return { content, loading };
}

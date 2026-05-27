'use client';

import { useEffect, useState } from 'react';

type BrandingState = {
  brand_name?: string;
  logo_url?: string;
  auth_tagline?: string;
  hero_headline?: string;
  hero_subheadline?: string;
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function usePublicBranding() {
  const [branding, setBranding] = useState<BrandingState>({});

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/public/site`, { cache: 'no-store' });
        if (!res.ok) return;
        const json = (await res.json()) as {
          data?: {
            landing?: {
              images?: BrandingState;
              hero?: { headline?: string; subheadline?: string };
            };
          };
        };
        const landing = json.data?.landing;
        if (cancelled || !landing) return;
        setBranding({
          ...landing.images,
          hero_headline: landing.hero?.headline,
          hero_subheadline: landing.hero?.subheadline,
        });
      } catch {
        /* noop */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return branding;
}

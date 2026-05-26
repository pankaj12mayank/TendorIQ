/** Server-side fetch for landing CMS (SEO + optional SSR hydrate). */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export type PublicSitePayload = {
  pricing?: Record<string, unknown>;
  landing?: {
    meta?: { title?: string; description?: string };
    hero?: Record<string, string>;
    social_proof?: { tagline?: string; logos?: string[] };
    features?: Array<{ title: string; description: string }>;
    testimonials?: Array<{ quote: string; author: string; role?: string; company?: string }>;
    faq?: Array<{ question: string; answer: string }>;
    cta?: { headline?: string; button?: string };
  };
};

export async function fetchPublicSite(): Promise<PublicSitePayload | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/public/site`, {
      next: { revalidate: 60 },
    });
    if (!res.ok) return null;
    const json = (await res.json()) as { data?: PublicSitePayload };
    return json.data ?? null;
  } catch {
    return null;
  }
}

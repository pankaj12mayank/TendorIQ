/** Server-side fetch for landing CMS (SEO + optional SSR hydrate). */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export type PublicSitePayload = {
  pricing?: Record<string, unknown>;
  landing?: {
    meta?: { title?: string; description?: string };
    hero?: Record<string, string>;
    pricing?: { title?: string; subtitle?: string; billing_note?: string };
    social_proof?: { tagline?: string; logos?: string[] };
    features?: Array<{ title: string; description: string }>;
    testimonials?: Array<{ quote: string; author: string; role?: string; company?: string }>;
    faq?: Array<{ question: string; answer: string }>;
    cta?: { headline?: string; button?: string };
    contact?: { title?: string; support_email?: string };
    customer_stories?: Array<{
      quote: string;
      author: string;
      role?: string;
      company?: string;
      logo_url?: string;
    }>;
    images?: {
      logo_url?: string;
      favicon_url?: string;
      hero_image_url?: string;
      auth_illustration_url?: string;
      brand_name?: string;
      auth_tagline?: string;
    };
    workflow_tutorial?: {
      title?: string;
      subtitle?: string;
      steps?: Array<{ id?: string; title?: string; description?: string }>;
    };
  };
  cms_state?: { version?: number; status?: string; published_at?: string | null };
  trust_stats?: {
    companies?: number;
    tenders_processed?: number;
    success_rate?: number;
    updated_at?: string | null;
  };
  updated_at?: string | null;
};

export async function fetchPublicSite(): Promise<PublicSitePayload | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/public/site`, {
      cache: 'no-store',
    });
    if (!res.ok) return null;
    const json = (await res.json()) as { data?: PublicSitePayload };
    return json.data ?? null;
  } catch {
    return null;
  }
}

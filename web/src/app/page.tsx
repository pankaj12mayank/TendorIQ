import type { Metadata } from 'next';

import { LandingPage } from '@/components/landing/landing-page';
import { fetchPublicSite } from '@/lib/public-site';

export async function generateMetadata(): Promise<Metadata> {
  const site = await fetchPublicSite();
  const meta = site?.landing?.meta;
  return {
    title: meta?.title ?? 'TenderIQ — AI Tender Analysis',
    description:
      meta?.description ??
      'Upload RFPs, analyze with your AI provider, and export proposal PDFs.',
    openGraph: {
      title: meta?.title ?? 'TenderIQ',
      description: meta?.description,
    },
  };
}

export default async function HomePage() {
  const initialSite = await fetchPublicSite();
  return <LandingPage initialSite={initialSite} />;
}

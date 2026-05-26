'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { authenticatedFetch } from '@/lib/api-fetch';
import { unwrapData } from '@/lib/api-envelope';

export interface ProposalSection {
  section_id: string;
  section_type: string;
  title: string;
  content: string;
  order: number;
  word_count?: number;
}

export interface TenderProposal {
  id: string;
  tender_id: string;
  title: string;
  status: string;
  sections: ProposalSection[];
  total_words?: number;
  model_used?: string;
  warnings?: string[];
}

export function useTenderProposal(tenderId?: string) {
  return useQuery({
    queryKey: ['proposal', tenderId],
    queryFn: async () => {
      if (!tenderId) return null;
      const res = await authenticatedFetch(`/api/v1/proposals/tender/${tenderId}`);
      if (!res.ok) throw new Error('Failed to load proposal');
      const data = unwrapData(await res.json());
      return (data as TenderProposal | null) ?? null;
    },
    enabled: Boolean(tenderId),
  });
}

export function useGenerateProposal(tenderId?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (opts?: { provider?: string; model?: string }) => {
      if (!tenderId) throw new Error('Missing tender ID');
      const res = await authenticatedFetch(`/api/v1/proposals/tender/${tenderId}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(opts ?? {}),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(
          (err as { error?: { message?: string } })?.error?.message ?? 'Generation failed'
        );
      }
      return unwrapData(await res.json()) as TenderProposal;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposal', tenderId] });
    },
  });
}

export async function downloadProposalPdf(proposalId: string): Promise<void> {
  const res = await authenticatedFetch(`/api/v1/proposals/${proposalId}/export/pdf`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('PDF export failed');
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `proposal-${proposalId.slice(0, 8)}.pdf`;
  a.click();
  URL.revokeObjectURL(url);
}

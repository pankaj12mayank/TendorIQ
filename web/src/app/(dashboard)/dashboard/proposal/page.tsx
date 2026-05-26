'use client';

import { useCallback, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { FileDown, Loader2, Sparkles } from 'lucide-react';
import { toast } from 'sonner';

import { PageHeader } from '@/components/design-system/page-header';
import { AiModelPicker } from '@/components/upload/ai-model-picker';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { authenticatedFetch } from '@/lib/api-fetch';
import { parseApiErrorMessage } from '@/lib/api-envelope';
import {
  downloadProposalPdf,
  useGenerateProposal,
  useTenderProposal,
  type ProposalSection,
} from '@/hooks/use-proposal';
import { mergePrefsWithLocal, useAiPreferences } from '@/hooks/use-ai-preferences';
import { ROUTES } from '@/lib/routes';

function SectionCard({
  section,
  onSave,
}: {
  section: ProposalSection;
  onSave: (id: string, content: string) => void;
}) {
  const [content, setContent] = useState(section.content);
  const [dirty, setDirty] = useState(false);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{section.title}</CardTitle>
        <CardDescription className="text-xs capitalize">{section.section_type.replace(/_/g, ' ')}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        <Textarea
          rows={8}
          value={content}
          onChange={(e) => {
            setContent(e.target.value);
            setDirty(true);
          }}
        />
        {dirty && (
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              onSave(section.section_id, content);
              setDirty(false);
            }}
          >
            Save section
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

export default function ProposalPage() {
  const searchParams = useSearchParams();
  const tenderId = searchParams.get('tenderId') ?? undefined;
  const { data: aiPrefs } = useAiPreferences();
  const selection = mergePrefsWithLocal(aiPrefs ?? undefined);
  const { data: proposal, isLoading, refetch } = useTenderProposal(tenderId);
  const generate = useGenerateProposal(tenderId);
  const [exporting, setExporting] = useState(false);

  const patchSection = useCallback(
    async (sectionId: string, content: string) => {
      if (!proposal?.id) return;
      const res = await authenticatedFetch(
        `/api/v1/proposals/${proposal.id}/sections/${sectionId}`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ content }),
        }
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        toast.error(parseApiErrorMessage(err) || 'Failed to save section');
        return;
      }
      toast.success('Section saved');
      void refetch();
    },
    [proposal?.id, refetch]
  );

  const handleGenerate = async () => {
    if (!tenderId) {
      toast.error('Open from analysis or upload with a tender ID');
      return;
    }
    try {
      await generate.mutateAsync({
        provider: selection.provider,
        model: selection.model,
      });
      toast.success('Proposal generated');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Generation failed');
    }
  };

  const handlePdf = async () => {
    if (!proposal?.id) return;
    setExporting(true);
    try {
      await downloadProposalPdf(proposal.id);
      toast.success('PDF downloaded');
    } catch {
      toast.error('PDF export failed — complete company profile in Settings');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title="Proposal"
        description={
          tenderId
            ? 'AI draft from tender analysis and your company profile.'
            : 'Add ?tenderId from Analysis or after upload to generate a proposal.'
        }
        actions={
          <div className="flex gap-2">
          {proposal?.id && (
            <Button variant="outline" onClick={handlePdf} disabled={exporting}>
              {exporting ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <FileDown className="mr-2 h-4 w-4" />
              )}
              Export PDF
            </Button>
          )}
          <Button onClick={handleGenerate} disabled={!tenderId || generate.isPending}>
            {generate.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="mr-2 h-4 w-4" />
            )}
            {proposal ? 'Regenerate' : 'Generate'} proposal
          </Button>
        </div>
        }
      />

      <Card className="border-border/80 shadow-sm">
        <CardHeader>
          <CardTitle className="text-base">AI model</CardTitle>
          <CardDescription>
            Defaults from{' '}
            <Link href={`${ROUTES.settings}/ai`} className="underline">
              Settings → AI
            </Link>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <AiModelPicker value={selection} showTest={false} />
        </CardContent>
      </Card>

      {isLoading && <p className="text-sm text-muted-foreground">Loading proposal…</p>}

      {proposal && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">{proposal.title}</h2>
            <span className="text-xs text-muted-foreground">
              {proposal.total_words ?? 0} words · {proposal.model_used ?? '—'}
            </span>
          </div>
          {proposal.sections?.map((section) => (
            <SectionCard key={section.section_id} section={section} onSave={patchSection} />
          ))}
        </div>
      )}

      {!isLoading && !proposal && tenderId && (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground text-sm">
            No proposal yet. Run analysis first, then click Generate.
          </CardContent>
        </Card>
      )}
    </div>
  );
}

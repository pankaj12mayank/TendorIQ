'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { FileDown, Loader2, Sparkles } from 'lucide-react';
import { appToast } from '@/lib/app-toast';

import { PageHeader } from '@/components/design-system/page-header';
import { AiModelPicker } from '@/components/upload/ai-model-picker';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import {
  downloadProposalPdf,
  autosaveProposal,
  useGenerateProposal,
  useTenderProposal,
  type ProposalSection,
} from '@/hooks/use-proposal';
import { mergePrefsWithLocal, useAiPreferences } from '@/hooks/use-ai-preferences';
import { ROUTES } from '@/lib/routes';

function SectionCard({
  section,
  onChange,
}: {
  section: ProposalSection;
  onChange: (id: string, content: string) => void;
}) {
  const [content, setContent] = useState(section.content);

  useEffect(() => {
    setContent(section.content);
  }, [section.content]);

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
            onChange(section.section_id, e.target.value);
          }}
        />
      </CardContent>
    </Card>
  );
}

export default function ProposalPage() {
  const searchParams = useSearchParams();
  const tenderId = searchParams.get('tenderId') ?? undefined;
  const { data: aiPrefs } = useAiPreferences();
  const selection = mergePrefsWithLocal(aiPrefs ?? undefined);
  const { data: proposal, isLoading } = useTenderProposal(tenderId);
  const generate = useGenerateProposal(tenderId);
  const [exporting, setExporting] = useState(false);
  const [draftSections, setDraftSections] = useState<ProposalSection[]>([]);
  const [autosaveState, setAutosaveState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    setDraftSections(proposal?.sections ?? []);
  }, [proposal?.sections]);

  useEffect(() => {
    return () => {
      if (saveTimer.current) clearTimeout(saveTimer.current);
    };
  }, []);

  const patchSection = useCallback(
    async (sectionId: string, content: string) => {
      const updated = draftSections.map((s) => (s.section_id === sectionId ? { ...s, content } : s));
      setDraftSections(updated);
      if (!proposal?.id) return;
      if (saveTimer.current) clearTimeout(saveTimer.current);
      setAutosaveState('saving');
      saveTimer.current = setTimeout(async () => {
        try {
          await autosaveProposal(proposal.id, { title: proposal.title, sections: updated });
          setAutosaveState('saved');
        } catch (err) {
          setAutosaveState('error');
          appToast.error(err instanceof Error ? err.message : 'Autosave failed');
        }
      }, 1200);
    },
    [draftSections, proposal?.id, proposal?.title]
  );

  const handleGenerate = async () => {
    if (!tenderId) {
      appToast.error('Open from analysis or upload with a tender ID.');
      return;
    }
    try {
      await generate.mutateAsync({
        provider: selection.provider,
        model: selection.model,
      });
      appToast.success('Proposal generated.');
    } catch (err) {
      appToast.error(err instanceof Error ? err.message : 'Generation failed');
    }
  };

  const handlePdf = async () => {
    if (!proposal?.id) return;
    setExporting(true);
    try {
      await downloadProposalPdf(proposal.id);
      appToast.success('PDF downloaded.');
    } catch (err) {
      appToast.error(
        err instanceof Error
          ? err.message
          : 'PDF export failed — complete company profile in Settings.'
      );
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
              {proposal.total_words ?? 0} words · {proposal.model_used ?? '—'} ·{' '}
              {autosaveState === 'saving'
                ? 'Saving...'
                : autosaveState === 'saved'
                  ? 'Saved'
                  : autosaveState === 'error'
                    ? 'Save failed'
                    : 'Idle'}
            </span>
          </div>
          {draftSections?.map((section) => (
            <SectionCard key={section.section_id} section={section} onChange={patchSection} />
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

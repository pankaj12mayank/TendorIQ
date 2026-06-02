'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { FileDown, Loader2, Sparkles } from 'lucide-react';
import { appToast } from '@/lib/app-toast';

import { SubscriptionGate } from '@/components/billing/subscription-gate';
import { PageHeader } from '@/components/design-system/page-header';
import { PremiumErrorState } from '@/components/design-system/empty-state';
import { LoadingState } from '@/components/ui/loading-state';
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
  const { data: proposal, isLoading, isError, error, refetch } = useTenderProposal(tenderId);
  const generate = useGenerateProposal(tenderId);
  const [exporting, setExporting] = useState(false);
  const [draftSections, setDraftSections] = useState<ProposalSection[]>([]);
  const [autosaveState, setAutosaveState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inFlightSave = useRef(false);
  const pendingAfterSave = useRef(false);
  const sectionsRef = useRef(draftSections);
  const proposalRef = useRef(proposal);

  useEffect(() => {
    setDraftSections(proposal?.sections ?? []);
  }, [proposal?.sections]);

  useEffect(() => {
    sectionsRef.current = draftSections;
  }, [draftSections]);

  useEffect(() => {
    proposalRef.current = proposal;
  }, [proposal]);

  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (autosaveState === 'saving') {
        e.preventDefault();
      }
    };
    window.addEventListener('beforeunload', handler);
    return () => {
      if (saveTimer.current) clearTimeout(saveTimer.current);
      window.removeEventListener('beforeunload', handler);
    };
  }, [autosaveState]);

  const doAutosave = useCallback(async () => {
    const p = proposalRef.current;
    if (!p?.id) return;
    if (inFlightSave.current) {
      pendingAfterSave.current = true;
      return;
    }
    inFlightSave.current = true;
    try {
      await autosaveProposal(p.id, { title: p.title, sections: sectionsRef.current });
      setAutosaveState('saved');
    } catch (err) {
      setAutosaveState('error');
      appToast.error(err instanceof Error ? err.message : 'Autosave failed');
    } finally {
      inFlightSave.current = false;
      if (pendingAfterSave.current) {
        pendingAfterSave.current = false;
        doAutosave();
      }
    }
  }, []);

  const scheduleAutosave = useCallback(() => {
    if (saveTimer.current) clearTimeout(saveTimer.current);
    setAutosaveState('saving');
    saveTimer.current = setTimeout(doAutosave, 1200);
  }, [doAutosave]);

  const patchSection = useCallback(
    (sectionId: string, content: string) => {
      setDraftSections((prev) => {
        const next = prev.map((s) => (s.section_id === sectionId ? { ...s, content } : s));
        sectionsRef.current = next;
        return next;
      });

      const p = proposalRef.current;
      if (!p?.id) return;

      scheduleAutosave();
    },
    [scheduleAutosave]
  );

  const handleGenerate = async () => {
    if (!tenderId) {
      appToast.error('Open from analysis or upload with a tender ID.');
      return;
    }
    try {
      await generate.mutateAsync({});
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
    <SubscriptionGate>
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

      {isLoading && <LoadingState message="Loading proposal..." />}

      {isError && !isLoading && (
        <PremiumErrorState
          title="Failed to load proposal"
          description={error instanceof Error ? error.message : 'Could not load proposal data'}
          onRetry={() => refetch()}
        />
      )}

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
    </SubscriptionGate>
  );
}

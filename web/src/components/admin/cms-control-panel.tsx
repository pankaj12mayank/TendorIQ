'use client';

import { useEffect, useMemo, useState } from 'react';
import { appToast } from '@/lib/app-toast';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useAdminPlatform, type LandingCmsState } from '@/hooks/use-admin-platform';
import { ArrowDown, ArrowUp, Trash2 } from 'lucide-react';

function toPairs(text: string) {
  return text
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [title, ...rest] = line.split('|');
      return { title: title?.trim() || '', description: rest.join('|').trim() };
    })
    .filter((x) => x.title && x.description);
}

function toFaq(text: string) {
  return text
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [question, ...rest] = line.split('|');
      return { question: question?.trim() || '', answer: rest.join('|').trim() };
    })
    .filter((x) => x.question && x.answer);
}

type Story = {
  quote: string;
  author: string;
  role?: string;
  company?: string;
  logo_url?: string;
};

type WorkflowDraftStep = {
  id: string;
  title: string;
  description: string;
  image_url?: string;
};

export function CmsControlPanel() {
  const { loadCms, saveCmsDraft, publishCms, rollbackCms, uploadCmsAsset } = useAdminPlatform();
  const [cms, setCms] = useState<LandingCmsState | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [rollbackId, setRollbackId] = useState<string>('');

  const [heroHeadline, setHeroHeadline] = useState('');
  const [heroSubheadline, setHeroSubheadline] = useState('');
  const [heroPrimary, setHeroPrimary] = useState('');
  const [heroSecondary, setHeroSecondary] = useState('');
  const [featuresText, setFeaturesText] = useState('');
  const [faqText, setFaqText] = useState('');
  const [ctaHeadline, setCtaHeadline] = useState('');
  const [ctaButton, setCtaButton] = useState('');
  const [pricingTitle, setPricingTitle] = useState('');
  const [pricingSubtitle, setPricingSubtitle] = useState('');
  const [logoUrl, setLogoUrl] = useState('');
  const [faviconUrl, setFaviconUrl] = useState('');
  const [heroImageUrl, setHeroImageUrl] = useState('');
  const [brandName, setBrandName] = useState('');
  const [workflowTitle, setWorkflowTitle] = useState('');
  const [workflowSubtitle, setWorkflowSubtitle] = useState('');
  const [supportEmail, setSupportEmail] = useState('');
  const [workflowSteps, setWorkflowSteps] = useState<WorkflowDraftStep[]>([]);
  const [stories, setStories] = useState<Story[]>([]);

  const hydrate = (state: LandingCmsState) => {
    setCms(state);
    const draft = (state.draft ?? {}) as Record<string, any>;
    const hero = draft.hero ?? {};
    const cta = draft.cta ?? {};
    const pricing = draft.pricing ?? {};
    const images = draft.images ?? {};
    const features = Array.isArray(draft.features) ? draft.features : [];
    const faq = Array.isArray(draft.faq) ? draft.faq : [];
    const workflow = draft.workflow_tutorial ?? {};
    const steps = Array.isArray(workflow.steps) ? workflow.steps : [];
    const customerStories = Array.isArray(draft.customer_stories) ? draft.customer_stories : [];
    setHeroHeadline(String(hero.headline ?? ''));
    setHeroSubheadline(String(hero.subheadline ?? ''));
    setHeroPrimary(String(hero.cta_primary ?? ''));
    setHeroSecondary(String(hero.cta_secondary ?? ''));
    setFeaturesText(features.map((f: any) => `${f.title ?? ''}|${f.description ?? ''}`).join('\n'));
    setFaqText(faq.map((f: any) => `${f.question ?? ''}|${f.answer ?? ''}`).join('\n'));
    setCtaHeadline(String(cta.headline ?? ''));
    setCtaButton(String(cta.button ?? ''));
    setPricingTitle(String(pricing.title ?? ''));
    setPricingSubtitle(String(pricing.subtitle ?? ''));
    setLogoUrl(String(images.logo_url ?? ''));
    setFaviconUrl(String(images.favicon_url ?? ''));
    setHeroImageUrl(String(images.hero_image_url ?? ''));
    setBrandName(String(images.brand_name ?? 'TenderIQ'));
    setWorkflowTitle(String(workflow.title ?? ''));
    setWorkflowSubtitle(String(workflow.subtitle ?? ''));
    setSupportEmail(String((draft.contact ?? {}).support_email ?? ''));
    setWorkflowSteps(
      steps.map((s: any, idx: number) => ({
        id: String(s.id ?? `step_${idx + 1}`),
        title: String(s.title ?? ''),
        description: String(s.description ?? ''),
        image_url: String(s.image_url ?? ''),
      }))
    );
    setStories(
      customerStories.map((story: any) => ({
        quote: String(story.quote ?? ''),
        author: String(story.author ?? ''),
        role: String(story.role ?? ''),
        company: String(story.company ?? ''),
        logo_url: String(story.logo_url ?? ''),
      }))
    );
  };

  useEffect(() => {
    (async () => {
      try {
        const state = await loadCms();
        hydrate(state);
      } catch (e) {
        appToast.error(e instanceof Error ? e.message : 'CMS load failed');
      } finally {
        setLoading(false);
      }
    })();
  }, [loadCms]);

  const revisionOptions = useMemo(() => cms?.history ?? [], [cms?.history]);

  function addWorkflowStep() {
    setWorkflowSteps((prev) => [...prev, { id: `step_${prev.length + 1}`, title: '', description: '', image_url: '' }]);
  }

  function reorderWorkflowStep(index: number, direction: -1 | 1) {
    setWorkflowSteps((prev) => {
      const to = index + direction;
      if (to < 0 || to >= prev.length) return prev;
      const next = [...prev];
      const [row] = next.splice(index, 1);
      next.splice(to, 0, row);
      return next;
    });
  }

  function updateWorkflowStep(index: number, patch: Partial<WorkflowDraftStep>) {
    setWorkflowSteps((prev) => prev.map((step, idx) => (idx === index ? { ...step, ...patch } : step)));
  }

  function removeWorkflowStep(index: number) {
    setWorkflowSteps((prev) => prev.filter((_, idx) => idx !== index));
  }

  function addStory() {
    setStories((prev) => [...prev, { quote: '', author: '', role: '', company: '', logo_url: '' }]);
  }

  function updateStory(index: number, patch: Partial<Story>) {
    setStories((prev) => prev.map((story, idx) => (idx === index ? { ...story, ...patch } : story)));
  }

  function removeStory(index: number) {
    setStories((prev) => prev.filter((_, idx) => idx !== index));
  }

  async function uploadStoryLogo(index: number, file?: File | null) {
    if (!file) return;
    try {
      const out = await uploadCmsAsset(file);
      const url = String((out as any).url ?? '');
      if (url) updateStory(index, { logo_url: url });
      appToast.success('Story logo uploaded.');
    } catch (e) {
      appToast.error(e instanceof Error ? e.message : 'Story logo upload failed');
    }
  }

  async function uploadWorkflowStepImage(index: number, file?: File | null) {
    if (!file) return;
    try {
      const out = await uploadCmsAsset(file);
      const url = String((out as any).url ?? '');
      if (url) updateWorkflowStep(index, { image_url: url });
      appToast.success('Workflow image uploaded.');
    } catch (e) {
      appToast.error(e instanceof Error ? e.message : 'Workflow image upload failed');
    }
  }

  async function saveDraft() {
    if (!cms) return;
    setSaving(true);
    try {
      const next = await saveCmsDraft(
        {
          hero: {
            headline: heroHeadline,
            subheadline: heroSubheadline,
            cta_primary: heroPrimary,
            cta_secondary: heroSecondary,
          },
          features: toPairs(featuresText),
          faq: toFaq(faqText),
          pricing: { title: pricingTitle, subtitle: pricingSubtitle },
          cta: { headline: ctaHeadline, button: ctaButton },
          contact: {
            title: 'Talk to our team',
            support_email: supportEmail,
          },
          customer_stories: stories
            .filter((x) => x.quote.trim() && x.author.trim())
            .map((x) => ({
              quote: x.quote.trim(),
              author: x.author.trim(),
              role: x.role?.trim() || '',
              company: x.company?.trim() || '',
              logo_url: x.logo_url?.trim() || '',
            })),
          images: {
            logo_url: logoUrl,
            favicon_url: faviconUrl,
            hero_image_url: heroImageUrl,
            brand_name: brandName,
          },
          workflow_tutorial: {
            title: workflowTitle,
            subtitle: workflowSubtitle,
            steps: workflowSteps
              .filter((step) => step.title.trim())
              .map((step, idx) => ({
                id: step.id || `step_${idx + 1}`,
                title: step.title.trim(),
                description: step.description.trim(),
                image_url: step.image_url?.trim() || '',
              })),
          },
        },
        cms.version
      );
      hydrate(next);
      appToast.success('CMS draft saved.');
    } catch (e) {
      appToast.error(e instanceof Error ? e.message : 'Draft save failed');
    } finally {
      setSaving(false);
    }
  }

  async function publish() {
    setSaving(true);
    try {
      const next = await publishCms();
      hydrate(next);
      appToast.success('CMS published.');
    } catch (e) {
      appToast.error(e instanceof Error ? e.message : 'Publish failed');
    } finally {
      setSaving(false);
    }
  }

  async function rollback() {
    if (!rollbackId) return;
    setSaving(true);
    try {
      const next = await rollbackCms(rollbackId);
      hydrate(next);
      appToast.success('Draft restored from revision.');
    } catch (e) {
      appToast.error(e instanceof Error ? e.message : 'Rollback failed');
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <p className="text-sm text-muted-foreground">Loading CMS…</p>;
  if (!cms) return <p className="text-sm text-destructive">CMS unavailable.</p>;

  return (
    <Card id="admin-panel-cms" role="tabpanel" aria-labelledby="admin-tab-cms">
      <CardHeader>
        <CardTitle>CMS Control</CardTitle>
        <CardDescription>
          Edit only live landing modules. Save draft first, then publish.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label>Hero headline</Label>
            <Input value={heroHeadline} onChange={(e) => setHeroHeadline(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>Hero subheadline</Label>
            <Input value={heroSubheadline} onChange={(e) => setHeroSubheadline(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>Hero primary button</Label>
            <Input value={heroPrimary} onChange={(e) => setHeroPrimary(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>Hero secondary button</Label>
            <Input value={heroSecondary} onChange={(e) => setHeroSecondary(e.target.value)} />
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label>Workflow title</Label>
            <Input value={workflowTitle} onChange={(e) => setWorkflowTitle(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>Workflow subtitle</Label>
            <Input value={workflowSubtitle} onChange={(e) => setWorkflowSubtitle(e.target.value)} />
          </div>
        </div>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label>Workflow steps (reorder supported)</Label>
            <Button type="button" variant="outline" onClick={addWorkflowStep}>
              Add step
            </Button>
          </div>
          {workflowSteps.map((step, index) => (
            <div key={`${step.id}-${index}`} className="grid gap-2 rounded-md border p-3 md:grid-cols-12">
              <Input
                className="md:col-span-3"
                placeholder="Step title"
                value={step.title}
                onChange={(e) => updateWorkflowStep(index, { title: e.target.value })}
              />
              <Input
                className="md:col-span-5"
                placeholder="Step description"
                value={step.description}
                onChange={(e) => updateWorkflowStep(index, { description: e.target.value })}
              />
              <Input
                className="md:col-span-3"
                placeholder="https://...step.webp"
                value={step.image_url || ''}
                onChange={(e) => updateWorkflowStep(index, { image_url: e.target.value })}
              />
              <div className="md:col-span-3">
                <Input
                  type="file"
                  accept="image/*"
                  onChange={(e) => void uploadWorkflowStepImage(index, e.target.files?.[0])}
                />
              </div>
              <div className="md:col-span-1 flex items-center gap-1 justify-end">
                <Button type="button" size="icon" variant="outline" onClick={() => reorderWorkflowStep(index, -1)}>
                  <ArrowUp className="h-4 w-4" />
                </Button>
                <Button type="button" size="icon" variant="outline" onClick={() => reorderWorkflowStep(index, 1)}>
                  <ArrowDown className="h-4 w-4" />
                </Button>
                <Button type="button" size="icon" variant="outline" onClick={() => removeWorkflowStep(index)}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>

        <div className="space-y-2">
          <Label>Features (one per line: title|description)</Label>
          <Textarea className="min-h-[120px]" value={featuresText} onChange={(e) => setFeaturesText(e.target.value)} />
        </div>

        <div className="space-y-2">
          <Label>FAQ (one per line: question|answer)</Label>
          <Textarea className="min-h-[120px]" value={faqText} onChange={(e) => setFaqText(e.target.value)} />
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label>Pricing title</Label>
            <Input value={pricingTitle} onChange={(e) => setPricingTitle(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>Pricing subtitle</Label>
            <Input value={pricingSubtitle} onChange={(e) => setPricingSubtitle(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>CTA headline</Label>
            <Input value={ctaHeadline} onChange={(e) => setCtaHeadline(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>CTA button text</Label>
            <Input value={ctaButton} onChange={(e) => setCtaButton(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>Support email (contact CTA)</Label>
            <Input value={supportEmail} onChange={(e) => setSupportEmail(e.target.value)} placeholder="support@company.com" />
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label>Customer stories</Label>
            <Button type="button" variant="outline" onClick={addStory}>
              Add story
            </Button>
          </div>
          {stories.map((story, index) => (
            <div key={`story-${index}`} className="grid gap-2 rounded-md border p-3 md:grid-cols-2">
              <Textarea
                className="md:col-span-2 min-h-[72px]"
                placeholder="Quote"
                value={story.quote}
                onChange={(e) => updateStory(index, { quote: e.target.value })}
              />
              <Input placeholder="Author" value={story.author} onChange={(e) => updateStory(index, { author: e.target.value })} />
              <Input placeholder="Role" value={story.role || ''} onChange={(e) => updateStory(index, { role: e.target.value })} />
              <Input
                placeholder="Company"
                value={story.company || ''}
                onChange={(e) => updateStory(index, { company: e.target.value })}
              />
              <Input
                placeholder="Logo URL (optional)"
                value={story.logo_url || ''}
                onChange={(e) => updateStory(index, { logo_url: e.target.value })}
              />
              <Input
                type="file"
                accept="image/*"
                onChange={(e) => void uploadStoryLogo(index, e.target.files?.[0])}
              />
              <div className="md:col-span-2 flex justify-end">
                <Button type="button" variant="outline" onClick={() => removeStory(index)}>
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </Button>
              </div>
            </div>
          ))}
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label>Logo URL</Label>
            <Input value={logoUrl} onChange={(e) => setLogoUrl(e.target.value)} placeholder="https://...logo.png" />
            <Input
              type="file"
              accept="image/*"
              onChange={async (e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                try {
                  const out = await uploadCmsAsset(file);
                  const url = String((out as any).url ?? '');
                  if (url) setLogoUrl(url);
                  appToast.success('Logo uploaded.');
                } catch (err) {
                  appToast.error(err instanceof Error ? err.message : 'Logo upload failed');
                }
              }}
            />
          </div>
          <div className="space-y-2">
            <Label>Favicon URL</Label>
            <Input value={faviconUrl} onChange={(e) => setFaviconUrl(e.target.value)} placeholder="https://...favicon.ico" />
            <Input
              type="file"
              accept="image/*"
              onChange={async (e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                try {
                  const out = await uploadCmsAsset(file);
                  const url = String((out as any).url ?? '');
                  if (url) setFaviconUrl(url);
                  appToast.success('Favicon uploaded.');
                } catch (err) {
                  appToast.error(err instanceof Error ? err.message : 'Favicon upload failed');
                }
              }}
            />
          </div>
          <div className="space-y-2">
            <Label>Hero image URL</Label>
            <Input value={heroImageUrl} onChange={(e) => setHeroImageUrl(e.target.value)} placeholder="https://...hero.webp" />
            <Input
              type="file"
              accept="image/*"
              onChange={async (e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                try {
                  const out = await uploadCmsAsset(file);
                  const url = String((out as any).url ?? '');
                  if (url) setHeroImageUrl(url);
                  appToast.success('Hero image uploaded.');
                } catch (err) {
                  appToast.error(err instanceof Error ? err.message : 'Hero image upload failed');
                }
              }}
            />
          </div>
          <div className="space-y-2">
            <Label>Brand name</Label>
            <Input value={brandName} onChange={(e) => setBrandName(e.target.value)} />
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button onClick={() => void saveDraft()} loading={saving} disabled={saving}>
            Save draft
          </Button>
          <Button variant="secondary" onClick={() => void publish()} loading={saving} disabled={saving}>
            Publish
          </Button>
          <Select value={rollbackId} onValueChange={setRollbackId}>
            <SelectTrigger className="w-72">
              <SelectValue placeholder="Select revision to rollback" />
            </SelectTrigger>
            <SelectContent>
              {revisionOptions.map((r) => (
                <SelectItem key={r.id} value={r.id}>
                  {r.id} (v{r.version})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={() => void rollback()} disabled={!rollbackId || saving}>
            Rollback
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

'use client';

import { useEffect, useState } from 'react';
import { toast } from 'sonner';

import { AiModelPicker } from '@/components/upload/ai-model-picker';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  mergePrefsWithLocal,
  useAiPreferences,
  useUpdateAiPreferences,
  type AiPreferences,
} from '@/hooks/use-ai-preferences';

export function AiPanel() {
  const { data: prefs, isLoading } = useAiPreferences();
  const updatePrefs = useUpdateAiPreferences();
  const [selection, setSelection] = useState<AiPreferences>(() => mergePrefsWithLocal());

  useEffect(() => {
    if (prefs) {
      setSelection(mergePrefsWithLocal(prefs));
    }
  }, [prefs]);

  const save = async () => {
    try {
      await updatePrefs.mutateAsync({
        provider: selection.provider,
        model: selection.model,
        style: selection.style,
        tone: selection.tone,
      });
      toast.success('AI preferences saved');
    } catch {
      toast.error('Failed to save preferences');
    }
  };

  return (
    <Card className="max-w-2xl">
      <CardHeader>
        <CardTitle>AI defaults</CardTitle>
        <CardDescription>Provider and model for upload, analysis, and proposals.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : (
          <>
            <AiModelPicker
              value={{ provider: selection.provider, model: selection.model }}
              onChange={(next) => setSelection((s) => ({ ...s, ...next }))}
            />
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label>Writing style</Label>
                <Select
                  value={selection.style ?? 'professional'}
                  onValueChange={(style) => setSelection((s) => ({ ...s, style }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="professional">Professional</SelectItem>
                    <SelectItem value="concise">Concise</SelectItem>
                    <SelectItem value="detailed">Detailed</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Tone</Label>
                <Select
                  value={selection.tone ?? 'formal'}
                  onValueChange={(tone) => setSelection((s) => ({ ...s, tone }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="formal">Formal</SelectItem>
                    <SelectItem value="friendly">Friendly</SelectItem>
                    <SelectItem value="persuasive">Persuasive</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <Button onClick={save} disabled={updatePrefs.isPending}>
              {updatePrefs.isPending ? 'Saving…' : 'Save defaults'}
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  );
}

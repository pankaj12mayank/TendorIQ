'use client';

import { Loader2, Sparkles, Wifi } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useAiCatalog, type AiSelection } from '@/hooks/use-ai-catalog';

interface AiModelPickerProps {
  value?: AiSelection;
  onChange?: (selection: AiSelection) => void;
  showTest?: boolean;
}

export function AiModelPicker({ value, onChange, showTest = true }: AiModelPickerProps) {
  const { catalog, loading, error, selection, updateSelection, testConnection } = useAiCatalog();
  const [testing, setTesting] = useState(false);

  const active = value ?? selection;
  const providerEntry = catalog?.providers.find((p) => p.id === active.provider);
  const models = providerEntry?.models ?? [];

  const handleProvider = (provider: string) => {
    const entry = catalog?.providers.find((p) => p.id === provider);
    const model = entry?.default_model ?? entry?.models[0] ?? active.model;
    const next = { provider, model };
    updateSelection(next);
    onChange?.(next);
  };

  const handleModel = (model: string) => {
    const next = { ...active, model };
    updateSelection(next);
    onChange?.(next);
  };

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading AI providers…
      </div>
    );
  }

  if (error) {
    return <p className="text-sm text-destructive">{error}</p>;
  }

  const configured = catalog?.providers.filter((p) => p.configured) ?? [];

  return (
    <div className="space-y-3 rounded-lg border bg-muted/30 p-4">
      <div className="flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-primary" />
        <span className="text-sm font-medium">AI analysis</span>
      </div>

      {configured.length === 0 ? (
        <p className="text-xs text-muted-foreground">
          Add <code className="text-xs">OPENAI_API_KEY</code>, <code className="text-xs">ANTHROPIC_API_KEY</code>,{' '}
          <code className="text-xs">GEMINI_API_KEY</code>, or run Ollama — then restart the API.
        </p>
      ) : (
        <>
          <div className="grid gap-2 sm:grid-cols-2">
            <div className="space-y-1">
              <Label className="text-xs">Provider</Label>
              <Select value={active.provider} onValueChange={handleProvider}>
                <SelectTrigger>
                  <SelectValue placeholder="Provider" />
                </SelectTrigger>
                <SelectContent>
                  {configured.map((p) => (
                    <SelectItem key={p.id} value={p.id}>
                      {p.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Model</Label>
              <Select value={active.model} onValueChange={handleModel}>
                <SelectTrigger>
                  <SelectValue placeholder="Model" />
                </SelectTrigger>
                <SelectContent>
                  {models.map((m) => (
                    <SelectItem key={m} value={m}>
                      {m}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {showTest && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={testing}
              onClick={async () => {
                setTesting(true);
                try {
                  await testConnection();
                  toast.success('AI connection OK');
                } catch (err) {
                  toast.error(err instanceof Error ? err.message : 'Test failed');
                } finally {
                  setTesting(false);
                }
              }}
            >
              {testing ? (
                <Loader2 className="mr-2 h-3 w-3 animate-spin" />
              ) : (
                <Wifi className="mr-2 h-3 w-3" />
              )}
              Test connection
            </Button>
          )}
        </>
      )}
    </div>
  );
}

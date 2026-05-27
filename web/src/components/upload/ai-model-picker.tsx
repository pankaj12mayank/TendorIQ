'use client';

import { CheckCircle2, Loader2, RefreshCw, Sparkles, Wifi, WifiOff } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { appToast } from '@/lib/app-toast';

import { Badge } from '@/components/ui/badge';
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
import { cn } from '@/lib/utils';

interface AiModelPickerProps {
  value?: AiSelection;
  onChange?: (selection: AiSelection) => void;
  showTest?: boolean;
  className?: string;
}

export function AiModelPicker({ value, onChange, showTest = true, className }: AiModelPickerProps) {
  const { catalog, loading, error, selection, updateSelection, refetch, testConnection } =
    useAiCatalog();
  const [testing, setTesting] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const lastNotified = useRef<string>('');

  const active = value ?? selection;
  const providerEntry = catalog?.providers.find((p) => p.id === active.provider);
  const models = providerEntry?.models ?? [];
  const configured = catalog?.providers.filter((p) => p.configured) ?? [];
  const ollamaEntry = catalog?.providers.find((p) => p.id === 'ollama');

  useEffect(() => {
    const key = `${selection.provider}:${selection.model}`;
    if (key === lastNotified.current) return;
    lastNotified.current = key;
    onChange?.(selection);
  }, [selection, onChange]);

  const handleProvider = (provider: string) => {
    const entry = catalog?.providers.find((p) => p.id === provider);
    const model =
      entry?.default_model && entry.models.includes(entry.default_model)
        ? entry.default_model
        : entry?.models[0] ?? active.model;
    const next = { provider, model };
    updateSelection(next);
    onChange?.(next);
  };

  const handleModel = (model: string) => {
    const next = { ...active, model };
    updateSelection(next);
    onChange?.(next);
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      const result = await refetch({ silent: true });
      if (result?.changed) {
        appToast.success('Model list updated from API.');
        onChange?.(result.next);
      } else {
        appToast.info('Model list is up to date.');
      }
    } catch {
      appToast.error('Could not refresh providers.');
    } finally {
      setRefreshing(false);
    }
  };

  if (loading && !catalog) {
    return (
      <div className={cn('flex items-center gap-2 rounded-xl border bg-card p-4 text-sm', className)}>
        <Loader2 className="h-4 w-4 animate-spin text-primary" />
        <span className="text-muted-foreground">Detecting AI providers…</span>
      </div>
    );
  }

  if (error && !catalog) {
    return (
      <div className={cn('rounded-xl border border-destructive/30 bg-destructive/5 p-4', className)}>
        <p className="text-sm text-destructive">{error}</p>
        <Button type="button" variant="outline" size="sm" className="mt-2" onClick={() => void refetch()}>
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className={cn('glass-panel space-y-4 p-4', className)}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
            <Sparkles className="h-4 w-4 text-primary" />
          </div>
          <div>
            <p className="text-sm font-semibold">AI model</p>
            <p className="text-xs text-muted-foreground">
              Auto-filled from active API keys and Ollama
            </p>
          </div>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          disabled={refreshing}
          onClick={() => void handleRefresh()}
        >
          {refreshing ? (
            <Loader2 className="mr-1 h-3 w-3 animate-spin" />
          ) : (
            <RefreshCw className="mr-1 h-3 w-3" />
          )}
          Refresh
        </Button>
      </div>

      <div className="flex flex-wrap gap-2">
        {catalog?.providers.map((p) => (
          <Badge
            key={p.id}
            variant={p.configured ? 'default' : 'outline'}
            className={cn(
              'text-xs font-normal',
              !p.configured && 'text-muted-foreground'
            )}
          >
            {p.configured ? (
              <CheckCircle2 className="mr-1 h-3 w-3" />
            ) : p.id === 'ollama' && p.online === false ? (
              <WifiOff className="mr-1 h-3 w-3" />
            ) : null}
            {p.label}
            {p.configured && p.models.length > 0 ? ` · ${p.models.length}` : ''}
          </Badge>
        ))}
      </div>

      {configured.length === 0 ? (
        <div className="rounded-lg bg-muted/50 p-3 text-xs text-muted-foreground space-y-1">
          <p>No AI provider is active yet.</p>
          <p>
            Add <code className="rounded bg-muted px-1">OPENAI_API_KEY</code> in{' '}
            <code className="rounded bg-muted px-1">.env</code>, or run{' '}
            <code className="rounded bg-muted px-1">ollama serve</code> and pull a model, then
            click Refresh.
          </p>
          {ollamaEntry?.hint && <p className="text-amber-600 dark:text-amber-400">{ollamaEntry.hint}</p>}
        </div>
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground">Provider</Label>
              <Select value={active.provider} onValueChange={handleProvider}>
                <SelectTrigger className="h-10">
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
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground">
                Model
                <span className="ml-1 font-normal text-primary">(auto)</span>
              </Label>
              <Select value={active.model} onValueChange={handleModel}>
                <SelectTrigger className="h-10">
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

          {providerEntry?.hint && (
            <p className="text-xs text-muted-foreground">{providerEntry.hint}</p>
          )}

          {showTest && (
            <Button
              type="button"
              variant="secondary"
              size="sm"
              disabled={testing || !active.model}
              onClick={async () => {
                setTesting(true);
                try {
                  await testConnection();
                  appToast.success(`Connected: ${active.provider} / ${active.model}.`);
                } catch (err) {
                  appToast.error(err instanceof Error ? err.message : 'Test failed');
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

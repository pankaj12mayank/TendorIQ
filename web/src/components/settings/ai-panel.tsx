'use client';

import { useEffect, useState } from 'react';
import { appToast } from '@/lib/app-toast';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { api } from '@/lib/api-client';

const PROVIDERS = ['openai', 'anthropic', 'gemini', 'ollama'];

export function AiPanel() {
  const [provider, setProvider] = useState('openai');
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState('');
  const [models, setModels] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [fetchingModels, setFetchingModels] = useState(false);
  const [prefsLoaded, setPrefsLoaded] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get('/api/v1/auth/me/ai-preferences');
        const data = res as any;
        if (data.provider) setProvider(data.provider);
        if (data.model) setModel(data.model);
      } catch { /* ignore */ }
      setPrefsLoaded(true);
      setLoading(false);
    })();
  }, []);

  const fetchModels = async () => {
    if (!apiKey.trim()) {
      appToast.warning('Enter an API key first.');
      return;
    }
    setFetchingModels(true);
    setModels([]);
    try {
      const res = await api.post('/api/v1/ai/fetch-models', { provider, api_key: apiKey.trim() });
      const data = res as any;
      if (data.models) {
        setModels(data.models);
        appToast.success(`Found ${data.models.length} models.`);
      }
    } catch (err) {
      appToast.error(err instanceof Error ? err.message : 'Failed to fetch models');
    } finally {
      setFetchingModels(false);
    }
  };

  const save = async () => {
    setLoading(true);
    try {
      await api.patch('/api/v1/auth/me/ai-preferences', {
        provider,
        api_key: apiKey.trim() || undefined,
        model: model || undefined,
      });
      appToast.success('AI settings saved.');
    } catch {
      appToast.error('Failed to save AI settings.');
    } finally {
      setLoading(false);
    }
  };

  if (!prefsLoaded) return null;

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>AI settings</CardTitle>
        <CardDescription>Enter your API key to connect to an AI provider. Fetch available models and select one.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6 max-w-xl">
        <div className="space-y-2">
          <Label htmlFor="ai-provider">Provider</Label>
          <Select value={provider} onValueChange={(v) => { setProvider(v); setModels([]); setModel(''); }}>
            <SelectTrigger id="ai-provider">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {PROVIDERS.map((p) => (
                <SelectItem key={p} value={p} className="capitalize">{p}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="ai-api-key">API key</Label>
          <div className="flex gap-2">
            <Input
              id="ai-api-key"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-..."
              className="flex-1"
            />
            <Button variant="outline" onClick={fetchModels} disabled={fetchingModels || !apiKey.trim()}>
              {fetchingModels ? 'Fetching...' : 'Fetch models'}
            </Button>
          </div>
        </div>

        {models.length > 0 && (
          <div className="space-y-2">
            <Label htmlFor="ai-model">Model</Label>
            <Select value={model} onValueChange={setModel}>
              <SelectTrigger id="ai-model">
                <SelectValue placeholder="Select a model" />
              </SelectTrigger>
              <SelectContent>
                {models.map((m) => (
                  <SelectItem key={m} value={m}>{m}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        <Button onClick={save} disabled={loading}>
          {loading ? 'Saving...' : 'Save settings'}
        </Button>
      </CardContent>
    </Card>
  );
}
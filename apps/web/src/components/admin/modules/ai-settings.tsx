'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/label';
import {
  Cpu,
  Plus,
  Trash2,
  CheckCircle,
  Save,
  RotateCcw,
} from 'lucide-react';
import { useAIProvidersApi } from '@/hooks/use-admin';
import { LoadingState } from '@/components/ui/loading-state';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

export function AISettings() {
  const {
    providers,
    isLoading,
    fetchProviders,
    addProvider,
    updateProvider,
    deleteProvider,
    toggleProvider,
    testProvider,
    updateSettings,
  } = useAIProvidersApi();

  const [showAdd, setShowAdd] = useState(false);
  const [newName, setNewName] = useState('');
  const [newType, setNewType] = useState('ollama');
  const [newBaseUrl, setNewBaseUrl] = useState('http://localhost:11434');
  const [newApiKey, setNewApiKey] = useState('');
  const [settings, setSettings] = useState({
    temperature: 0.7,
    maxTokens: 2048,
    topP: 1,
    frequencyPenalty: 0,
    presencePenalty: 0,
  });

  const defaultProvider = providers.find((p) => p.isActive) ?? providers[0];

  useEffect(() => {
    void fetchProviders();
  }, [fetchProviders]);

  useEffect(() => {
    if (defaultProvider?.settings) {
      setSettings(defaultProvider.settings);
    }
  }, [defaultProvider?.id]);

  if (isLoading && providers.length === 0) {
    return <LoadingState message="Loading AI providers..." />;
  }

  async function handleAdd() {
    if (!newName.trim()) {
      toast.error('Provider name is required');
      return;
    }
    await addProvider({
      name: newName,
      type: newType as 'ollama' | 'openai' | 'anthropic',
      base_url: newBaseUrl,
      api_key: newApiKey || undefined,
      isActive: true,
    } as Parameters<typeof addProvider>[0]);
    setShowAdd(false);
    setNewName('');
    setNewApiKey('');
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">AI Settings</h2>
          <p className="text-muted-foreground">
            Manage providers — Ollama is the default for local testing. API keys are stored encrypted.
          </p>
        </div>
        <Button onClick={() => setShowAdd(!showAdd)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Provider
        </Button>
      </div>

      {showAdd && (
        <Card>
          <CardHeader>
            <CardTitle>New provider</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div>
              <Label>Name</Label>
              <Input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Ollama Local" />
            </div>
            <div>
              <Label>Type</Label>
              <select
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                value={newType}
                onChange={(e) => setNewType(e.target.value)}
              >
                <option value="ollama">Ollama</option>
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="gemini">Gemini</option>
              </select>
            </div>
            <div>
              <Label>Base URL</Label>
              <Input value={newBaseUrl} onChange={(e) => setNewBaseUrl(e.target.value)} />
            </div>
            <div>
              <Label>API key (optional)</Label>
              <Input type="password" value={newApiKey} onChange={(e) => setNewApiKey(e.target.value)} />
            </div>
            <div className="md:col-span-2 flex gap-2">
              <Button onClick={() => void handleAdd()}>Save provider</Button>
              <Button variant="outline" onClick={() => setShowAdd(false)}>
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>AI Providers</CardTitle>
            <CardDescription>Test, activate, or remove providers</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {providers.length === 0 ? (
              <p className="text-sm text-muted-foreground">No providers configured yet.</p>
            ) : (
              providers.map((provider) => (
                <div key={provider.id} className="rounded-lg border p-4">
                  <div className="mb-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div
                        className={cn(
                          'flex h-10 w-10 items-center justify-center rounded-lg',
                          provider.isActive ? 'bg-green-100' : 'bg-muted'
                        )}
                      >
                        <Cpu className={cn('h-5 w-5', provider.isActive ? 'text-green-600' : 'text-muted-foreground')} />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold">{provider.name}</h3>
                          <Badge variant="outline">{provider.type}</Badge>
                          {provider.id === 'ollama' && (
                            <Badge className="bg-primary/10 text-primary">Default</Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground">
                          Key: {provider.apiKeyMasked || 'not set'}
                        </p>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Button variant="outline" size="sm" onClick={() => void testProvider(provider.id)}>
                        Test
                      </Button>
                      <Button
                        variant={provider.isActive ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => void toggleProvider(provider.id)}
                      >
                        {provider.isActive ? 'Active' : 'Activate'}
                      </Button>
                      {provider.id !== 'ollama' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-destructive"
                          onClick={() => void deleteProvider(provider.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                  {provider.models?.length > 0 && (
                    <div className="grid gap-2 md:grid-cols-2">
                      {provider.models.map((model) => (
                        <div key={model.id} className="rounded-lg bg-muted p-3 text-sm">
                          <p className="font-medium">{model.name}</p>
                          <p className="text-xs text-muted-foreground">
                            Max {model.maxTokens.toLocaleString()} tokens
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Model parameters</CardTitle>
            <CardDescription>
              {defaultProvider ? `For ${defaultProvider.name}` : 'Select an active provider'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Temperature: {settings.temperature}</Label>
              <Slider
                value={[settings.temperature]}
                onValueChange={([v]) =>
                  setSettings((s) => ({ ...s, temperature: v ?? s.temperature }))
                }
                max={2}
                step={0.1}
              />
            </div>
            <div>
              <Label>Max tokens: {settings.maxTokens}</Label>
              <Slider
                value={[settings.maxTokens]}
                onValueChange={([v]) =>
                  setSettings((s) => ({ ...s, maxTokens: v ?? s.maxTokens }))
                }
                min={256}
                max={8192}
                step={256}
              />
            </div>
            <Button
              className="w-full"
              disabled={!defaultProvider}
              onClick={() =>
                defaultProvider && void updateSettings(defaultProvider.id, settings)
              }
            >
              <Save className="mr-2 h-4 w-4" />
              Save settings
            </Button>
            <Button
              variant="outline"
              className="w-full"
              onClick={() => defaultProvider?.settings && setSettings(defaultProvider.settings)}
            >
              <RotateCcw className="mr-2 h-4 w-4" />
              Reset
            </Button>
            <div className="flex items-center gap-2 text-sm text-green-600">
              <CheckCircle className="h-4 w-4" />
              Changes sync to platform storage
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

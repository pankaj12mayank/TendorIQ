'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import {
  Cpu,
  Plus,
  Edit3,
  Trash2,
  Settings,
  CheckCircle,
  XCircle,
  Key,
  Save,
  RotateCcw,
} from 'lucide-react';
import { AIProvider, AIModel } from '../types';
import { MOCK_AI_PROVIDERS } from '../constants';
import { cn } from '@/lib/utils';

export function AISettings() {
  const [providers, setProviders] = useState<AIProvider[]>(MOCK_AI_PROVIDERS);
  const [editingProvider, setEditingProvider] = useState<string | null>(null);
  const [settings, setSettings] = useState({
    temperature: 0.7,
    maxTokens: 2048,
    topP: 1,
    frequencyPenalty: 0,
    presencePenalty: 0,
  });

  const toggleProvider = (id: string) => {
    setProviders(providers.map((p) =>
      p.id === id ? { ...p, isActive: !p.isActive } : p
    ));
  };

  const updateSetting = (key: string, value: number) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">AI Settings</h2>
          <p className="text-muted-foreground">Configure AI providers and model parameters</p>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          Add Provider
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>AI Providers</CardTitle>
            <CardDescription>Manage your AI service providers and models</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {providers.map((provider) => (
                <div key={provider.id} className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className={cn(
                        'w-10 h-10 rounded-lg flex items-center justify-center',
                        provider.isActive ? 'bg-green-100' : 'bg-gray-100'
                      )}>
                        <Cpu className={cn('w-5 h-5', provider.isActive ? 'text-green-600' : 'text-gray-400')} />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold">{provider.name}</h3>
                          <Badge variant="outline">{provider.type}</Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">API Key: {provider.apiKeyMasked}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant={provider.isActive ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => toggleProvider(provider.id)}
                      >
                        {provider.isActive ? 'Active' : 'Deactivate'}
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Edit3 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">Available Models</h4>
                    <div className="grid gap-2 md:grid-cols-2">
                      {provider.models.map((model) => (
                        <div key={model.id} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                          <div>
                            <p className="font-medium">{model.name}</p>
                            <p className="text-xs text-muted-foreground">
                              Max: {model.maxTokens.toLocaleString()} tokens | ${model.costPer1kTokens}/1K tokens
                            </p>
                          </div>
                          {model.isDefault && (
                            <Badge className="bg-primary text-primary-foreground">Default</Badge>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5" />
                Model Parameters
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium">Temperature</label>
                  <span className="text-sm text-muted-foreground">{settings.temperature}</span>
                </div>
                <Slider
                  value={[settings.temperature * 10]}
                  min={0}
                  max={20}
                  step={1}
                  onValueChange={(v) => updateSetting('temperature', v[0] / 10)}
                />
                <p className="text-xs text-muted-foreground">Lower = more focused, Higher = more creative</p>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium">Max Tokens</label>
                  <span className="text-sm text-muted-foreground">{settings.maxTokens}</span>
                </div>
                <Slider
                  value={[settings.maxTokens / 100]}
                  min={100}
                  max={16000}
                  step={100}
                  onValueChange={(v) => updateSetting('maxTokens', v[0] * 100)}
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium">Top P</label>
                  <span className="text-sm text-muted-foreground">{settings.topP}</span>
                </div>
                <Slider
                  value={[settings.topP * 10]}
                  min={0}
                  max={10}
                  step={1}
                  onValueChange={(v) => updateSetting('topP', v[0] / 10)}
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium">Frequency Penalty</label>
                  <span className="text-sm text-muted-foreground">{settings.frequencyPenalty}</span>
                </div>
                <Slider
                  value={[settings.frequencyPenalty * 10 + 10]}
                  min={0}
                  max={20}
                  step={1}
                  onValueChange={(v) => updateSetting('frequencyPenalty', (v[0] - 10) / 10)}
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium">Presence Penalty</label>
                  <span className="text-sm text-muted-foreground">{settings.presencePenalty}</span>
                </div>
                <Slider
                  value={[settings.presencePenalty * 10 + 10]}
                  min={0}
                  max={20}
                  step={1}
                  onValueChange={(v) => updateSetting('presencePenalty', (v[0] - 10) / 10)}
                />
              </div>

              <div className="flex gap-2 pt-4">
                <Button className="flex-1">
                  <Save className="w-4 h-4 mr-2" />
                  Save
                </Button>
                <Button variant="outline">
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Reset
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>API Key Management</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                <Key className="w-5 h-5 text-muted-foreground" />
                <div className="flex-1">
                  <p className="text-sm font-medium">OpenAI API Key</p>
                  <p className="text-xs text-muted-foreground">sk-****-xxxx</p>
                </div>
                <Button variant="ghost" size="sm">Rotate</Button>
              </div>
              <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                <Key className="w-5 h-5 text-muted-foreground" />
                <div className="flex-1">
                  <p className="text-sm font-medium">Anthropic API Key</p>
                  <p className="text-xs text-muted-foreground">sk-****-xxxx</p>
                </div>
                <Button variant="ghost" size="sm">Rotate</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default AISettings;
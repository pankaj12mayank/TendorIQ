'use client';

import React, { useState, useEffect } from 'react';
import { usePromptsApi } from '@/hooks/use-admin';
import { LoadingState } from '@/components/ui/loading-state';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  MessageSquare,
  Plus,
  Edit3,
  Trash2,
  Copy,
  Search,
  Filter,
  Code,
  Play,
  History,
  Variable,
} from 'lucide-react';
import { PromptTemplate } from '../types';
import { cn } from '@/lib/utils';

const CATEGORY_COLORS = {
  extraction: 'bg-blue-100 text-blue-800',
  analysis: 'bg-purple-100 text-purple-800',
  summary: 'bg-green-100 text-green-800',
  risk: 'bg-orange-100 text-orange-800',
  custom: 'bg-gray-100 text-gray-800',
};

export function PromptManagement() {
  const { prompts, isLoading, fetchPrompts, togglePromptActive, deletePrompt } = usePromptsApi();

  useEffect(() => {
    void fetchPrompts();
  }, [fetchPrompts]);

  if (isLoading && prompts.length === 0) {
    return <LoadingState message="Loading prompts..." />;
  }
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null);
  const [selectedPrompt, setSelectedPrompt] = useState<PromptTemplate | null>(null);

  const filteredPrompts = prompts.filter((prompt) => {
    const matchesSearch = prompt.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      prompt.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = !categoryFilter || prompt.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });


  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Prompt Management</h2>
          <p className="text-muted-foreground">Manage AI prompt templates</p>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          Create Template
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="relative flex-1 max-w-sm">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="Search prompts..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <select
                  className="h-10 px-3 rounded-md border bg-background text-sm"
                  value={categoryFilter || ''}
                  onChange={(e) => setCategoryFilter(e.target.value || null)}
                >
                  <option value="">All Categories</option>
                  <option value="extraction">Extraction</option>
                  <option value="analysis">Analysis</option>
                  <option value="summary">Summary</option>
                  <option value="risk">Risk</option>
                  <option value="custom">Custom</option>
                </select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {filteredPrompts.map((prompt) => (
                <div
                  key={prompt.id}
                  className={cn(
                    'p-4 border rounded-lg cursor-pointer transition-all',
                    selectedPrompt?.id === prompt.id
                      ? 'border-primary bg-primary/5'
                      : 'hover:border-primary/50'
                  )}
                  onClick={() => setSelectedPrompt(prompt)}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <MessageSquare className="w-5 h-5 text-muted-foreground" />
                      <h3 className="font-semibold">{prompt.name}</h3>
                      <Badge className={CATEGORY_COLORS[prompt.category]}>
                        {prompt.category}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={prompt.isActive ? 'default' : 'outline'}>
                        {prompt.isActive ? 'Active' : 'Inactive'}
                      </Badge>
                      <span className="text-xs text-muted-foreground">v{prompt.version}</span>
                    </div>
                  </div>
                  <p className="text-sm text-muted-foreground mb-3">{prompt.description}</p>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span>{prompt.variables.length} variables</span>
                      <span>By: {prompt.createdBy}</span>
                      <span>Updated: {prompt.updatedAt}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button variant="ghost" size="sm">
                        <Play className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Edit3 className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Copy className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Prompt Details</CardTitle>
          </CardHeader>
          <CardContent>
            {selectedPrompt ? (
              <div className="space-y-4">
                <div>
                  <h3 className="font-semibold mb-2">{selectedPrompt.name}</h3>
                  <p className="text-sm text-muted-foreground">{selectedPrompt.description}</p>
                </div>

                <div>
                  <h4 className="text-sm font-medium mb-2">Template Content</h4>
                  <div className="p-3 bg-muted rounded-lg font-mono text-sm whitespace-pre-wrap">
                    {selectedPrompt.content}
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                    <Variable className="w-4 h-4" />
                    Variables
                  </h4>
                  <div className="space-y-2">
                    {selectedPrompt.variables.map((variable) => (
                      <div key={variable.name} className="p-2 border rounded text-sm">
                        <div className="flex items-center justify-between">
                          <span className="font-mono">{variable.name}</span>
                          <Badge variant="outline" className="text-xs">{variable.type}</Badge>
                        </div>
                        {variable.options && (
                          <p className="text-xs text-muted-foreground mt-1">
                            Options: {variable.options.join(', ')}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex gap-2 pt-4">
                  <Button className="flex-1">
                    <Play className="w-4 h-4 mr-2" />
                    Test
                  </Button>
                  <Button variant="outline">
                    <Edit3 className="w-4 h-4 mr-2" />
                    Edit
                  </Button>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                Select a prompt to view details
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Template Categories</CardTitle>
          <CardDescription>Organize your prompts by category</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-5">
            {Object.entries(CATEGORY_COLORS).map(([category, color]) => {
              const count = prompts.filter((p) => p.category === category).length;
              return (
                <div key={category} className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <Badge className={color}>{category}</Badge>
                    <span className="text-2xl font-bold">{count}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {count === 0 ? 'No templates' : `${count} template${count > 1 ? 's' : ''}`}
                  </p>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default PromptManagement;
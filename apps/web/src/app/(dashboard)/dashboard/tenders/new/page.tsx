'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ChevronLeft, Loader2 } from 'lucide-react';

import { CanCreateTender } from '@/components/auth/rbac';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useCreateTender } from '@/hooks/use-api';

export default function NewTenderPage() {
  const router = useRouter();
  const createTender = useCreateTender();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [budget, setBudget] = useState('');
  const [closingDate, setClosingDate] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !description.trim()) return;

    const tender = await createTender.mutateAsync({
      title: title.trim(),
      description: description.trim(),
      status: 'draft',
      budget: budget ? Number(budget) : null,
      currency: 'USD',
      closingDate: closingDate ? new Date(closingDate).toISOString() : null,
    });

    router.push(`/dashboard/tenders/analysis?tenderId=${tender.id}`);
  };

  return (
    <CanCreateTender
      fallback={
        <div className="py-12 text-center text-muted-foreground">
          You do not have permission to create tenders.
        </div>
      }
    >
      <div className="mx-auto max-w-2xl space-y-6">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" asChild>
            <Link href="/dashboard/tenders">
              <ChevronLeft className="h-5 w-5" />
            </Link>
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Create tender</h1>
            <p className="text-muted-foreground">Add a new procurement opportunity to your workspace.</p>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Tender details</CardTitle>
            <CardDescription>Required fields are saved to your tenant via the API.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="title">Title</Label>
                <Input
                  id="title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Municipal water infrastructure RFP"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Scope, requirements, and evaluation notes"
                  rows={5}
                  required
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="budget">Budget (optional)</Label>
                  <Input
                    id="budget"
                    type="number"
                    min={0}
                    step="0.01"
                    value={budget}
                    onChange={(e) => setBudget(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="closing">Closing date (optional)</Label>
                  <Input
                    id="closing"
                    type="date"
                    value={closingDate}
                    onChange={(e) => setClosingDate(e.target.value)}
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="outline" asChild>
                  <Link href="/dashboard/tenders">Cancel</Link>
                </Button>
                <Button type="submit" disabled={createTender.isPending}>
                  {createTender.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Create tender
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </CanCreateTender>
  );
}

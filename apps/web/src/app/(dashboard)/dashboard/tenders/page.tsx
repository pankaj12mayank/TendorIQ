'use client';

import Link from 'next/link';
import { FileText, Plus, Search, Loader2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { CanCreateTender } from '@/components/auth/rbac';
import { useTenders } from '@/hooks/use-api';
import { formatTenderDeadline, formatTenderValue } from '@/lib/api-envelope';
import { PremiumErrorState } from '@/components/design-system/empty-state';

export default function TendersPage() {
  const { data, isLoading, isError, refetch } = useTenders();
  const tenders = data?.data ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Tenders</h1>
          <p className="text-muted-foreground">Manage your tender documents and proposals.</p>
        </div>
        <CanCreateTender>
          <Button asChild>
            <Link href="/dashboard/tenders/new">
              <Plus className="w-4 h-4 mr-2" />
              Create Tender
            </Link>
          </Button>
        </CanCreateTender>
      </div>

      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input placeholder="Search tenders..." className="pl-10" />
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
        </div>
      ) : isError ? (
        <PremiumErrorState onRetry={() => refetch()} />
      ) : tenders.length === 0 ? (
        <p className="text-center text-muted-foreground py-12">No tenders yet. Create your first tender.</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {tenders.map((tender) => (
            <Card key={tender.id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <FileText className="w-8 h-8 text-blue-500" />
                  <span
                    className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      tender.status === 'published'
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                        : tender.status === 'draft'
                        ? 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300'
                        : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
                    }`}
                  >
                    {tender.status.replace('_', ' ')}
                  </span>
                </div>
                <CardTitle className="mt-4">
                  <Link
                    href={`/dashboard/tenders/analysis?tenderId=${tender.id}`}
                    className="hover:underline"
                  >
                    {tender.title}
                  </Link>
                </CardTitle>
                <CardDescription>Tender ID: {tender.id}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Value: {formatTenderValue(tender)}</span>
                  <span className="text-muted-foreground">Deadline: {formatTenderDeadline(tender)}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

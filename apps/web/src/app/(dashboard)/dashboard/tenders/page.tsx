'use client';

import { FileText, Plus, Search } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

const mockTenders = [
  { id: '1', title: 'IT Infrastructure Upgrade', status: 'published', deadline: '2026-06-15', value: '$500,000' },
  { id: '2', title: 'Office Supplies Procurement', status: 'draft', deadline: '2026-06-20', value: '$50,000' },
  { id: '3', title: 'Marketing Services RFP', status: 'published', deadline: '2026-06-25', value: '$150,000' },
  { id: '4', title: 'Cloud Migration Project', status: 'under_review', deadline: '2026-07-01', value: '$300,000' },
];

export default function TendersPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Tenders</h1>
          <p className="text-muted-foreground">Manage your tender documents and proposals.</p>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          Create Tender
        </Button>
      </div>

      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input placeholder="Search tenders..." className="pl-10" />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {mockTenders.map((tender) => (
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
              <CardTitle className="mt-4">{tender.title}</CardTitle>
              <CardDescription>Tender ID: {tender.id}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Value: {tender.value}</span>
                <span className="text-muted-foreground">Deadline: {tender.deadline}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
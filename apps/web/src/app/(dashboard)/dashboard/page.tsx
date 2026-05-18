'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useTenders } from '@/hooks/use-api';
import { LoadingState } from '@/components/ui/loading-state';
import { ErrorState } from '@/components/ui/error-state';
import { FileText, Users, TrendingUp, DollarSign } from 'lucide-react';

export default function DashboardPage() {
  const { data, isLoading, isError, refetch } = useTenders({ limit: 5 });

  const stats = [
    { title: 'Total Tenders', value: '24', icon: FileText, trend: '+12%' },
    { title: 'Active Bids', value: '18', icon: TrendingUp, trend: '+5%' },
    { title: 'Organizations', value: '3', icon: Users, trend: '0%' },
    { title: 'Total Value', value: '$2.4M', icon: DollarSign, trend: '+18%' },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">Overview of your tender management activities.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground">
                <span className="text-green-600">{stat.trend}</span> from last month
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Tenders</CardTitle>
            <CardDescription>Your latest tender activities.</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <LoadingState message="Loading tenders..." />
            ) : isError ? (
              <ErrorState onRetry={() => refetch()} />
            ) : (
              <div className="space-y-4">
                {data?.data.map((tender) => (
                  <div
                    key={tender.id}
                    className="flex items-center justify-between border-b pb-3 last:border-0"
                  >
                    <div className="space-y-1">
                      <p className="text-sm font-medium leading-none">{tender.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(tender.createdAt).toLocaleDateString()}
                      </p>
                    </div>
                    <span
                      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                        tender.status === 'published'
                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                          : tender.status === 'draft'
                          ? 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300'
                          : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
                      }`}
                    >
                      {tender.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common tasks at your fingertips.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-2">
            <a
              href="/dashboard/tenders/new"
              className="flex items-center gap-3 rounded-lg border p-3 transition-colors hover:bg-muted"
            >
              <FileText className="h-5 w-5" />
              <span className="text-sm font-medium">Create New Tender</span>
            </a>
            <a
              href="/dashboard/bids"
              className="flex items-center gap-3 rounded-lg border p-3 transition-colors hover:bg-muted"
            >
              <TrendingUp className="h-5 w-5" />
              <span className="text-sm font-medium">View Active Bids</span>
            </a>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
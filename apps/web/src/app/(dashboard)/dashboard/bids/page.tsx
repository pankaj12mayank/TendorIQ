'use client';

import { TrendingUp, DollarSign, Clock, CheckCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const mockBids = [
  { id: '1', tender: 'IT Infrastructure Upgrade', amount: '$485,000', status: 'submitted', submittedAt: '2026-05-15' },
  { id: '2', tender: 'Office Supplies Procurement', amount: '$48,500', status: 'won', submittedAt: '2026-05-10' },
  { id: '3', tender: 'Marketing Services RFP', amount: '$140,000', status: 'under_review', submittedAt: '2026-05-12' },
];

export default function BidsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">My Bids</h1>
        <p className="text-muted-foreground">Track your tender submissions and their status.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Bids</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">12</div>
            <p className="text-xs text-muted-foreground">+3 this month</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Win Rate</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">75%</div>
            <p className="text-xs text-muted-foreground">+5% from last quarter</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Value</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">$2.1M</div>
            <p className="text-xs text-muted-foreground">Across all bids</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">4</div>
            <p className="text-xs text-muted-foreground">Awaiting response</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Bids</CardTitle>
          <CardDescription>Your latest tender submissions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {mockBids.map((bid) => (
              <div key={bid.id} className="flex items-center justify-between border-b pb-4 last:border-0">
                <div className="space-y-1">
                  <p className="font-medium">{bid.tender}</p>
                  <p className="text-sm text-muted-foreground">Bid Amount: {bid.amount}</p>
                  <p className="text-xs text-muted-foreground">Submitted: {bid.submittedAt}</p>
                </div>
                <Badge
                  variant={
                    bid.status === 'won'
                      ? 'default'
                      : bid.status === 'submitted'
                      ? 'secondary'
                      : 'outline'
                  }
                >
                  {bid.status.replace('_', ' ')}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
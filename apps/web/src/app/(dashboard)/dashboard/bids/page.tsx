'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, DollarSign, Clock, CheckCircle, Loader2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api-client';

interface Bid {
  id: string;
  tender: string;
  amount: string;
  status: string;
  submittedAt: string;
}

export default function BidsPage() {
  const [bids, setBids] = useState<Bid[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchBids = async () => {
      try {
        const res = await api.get<{ bids: Bid[]; total_bids: number; win_rate: number; total_value: string; pending_count: number }>('/api/v1/bids');
        setBids(res.bids);
      } catch (err) {
        setError('Failed to load bids');
      } finally {
        setLoading(false);
      }
    };
    fetchBids();
  }, []);

  const totalBids = bids.length;
  const wonBids = bids.filter(b => b.status === 'won').length;
  const winRate = totalBids > 0 ? Math.round((wonBids / totalBids) * 100) : 0;
  const pendingCount = bids.filter(b => b.status === 'submitted' || b.status === 'under_review').length;
  const totalValue = bids.reduce((sum, b) => {
    const num = parseFloat(b.amount.replace(/[$,]/g, ''));
    return sum + (isNaN(num) ? 0 : num);
  }, 0);

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
            <div className="text-2xl font-bold">{totalBids}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Win Rate</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{winRate}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Value</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${totalValue.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">Across all bids</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingCount}</div>
            <p className="text-xs text-muted-foreground">Awaiting response</p>
          </CardContent>
        </Card>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <p className="text-destructive text-center py-12">{error}</p>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Recent Bids</CardTitle>
            <CardDescription>Your latest tender submissions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {bids.map((bid) => (
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
      )}
    </div>
  );
}
'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  Shield,
  Plus,
  Minus,
  Clock,
  User,
  CheckCircle,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Search,
  Filter,
} from 'lucide-react';
import { AdminQuotaOverride, FeatureKey } from '../types';
import { useAdminOverride } from '../hooks/use-usage';
import { useUsageStore } from '../store';
import { FEATURE_CONFIG } from '../constants';
import { cn } from '@/lib/utils';

interface AdminOverridePanelProps {
  className?: string;
}

export function AdminOverridePanel({ className }: AdminOverridePanelProps) {
  const { overrides, createOverride, revokeOverride, getOverridesForUser } = useAdminOverride();
  const [selectedUser, setSelectedUser] = useState<string>('');
  const [showCreateForm, setShowCreateForm] = useState(false);

  return (
    <Card className={cn(className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Shield className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <CardTitle>Admin Overrides</CardTitle>
              <CardDescription>Manage quota overrides for users</CardDescription>
            </div>
          </div>
          <Button size="sm" onClick={() => setShowCreateForm(!showCreateForm)}>
            <Plus className="w-4 h-4 mr-2" />
            Add Override
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {showCreateForm && (
          <OverrideCreateForm
            onSubmit={async (request) => {
              await createOverride(request);
              setShowCreateForm(false);
            }}
            onCancel={() => setShowCreateForm(false)}
          />
        )}

        {overrides.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Shield className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No active overrides</p>
          </div>
        ) : (
          <div className="space-y-3">
            {overrides.map((override) => (
              <OverrideCard
                key={override.id}
                override={override}
                onRevoke={() => revokeOverride(override.id)}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface OverrideCreateFormProps {
  onSubmit: (request: { userId: string; featureKey: FeatureKey; newLimit: number; reason: string; duration?: string }) => void;
  onCancel: () => void;
}

export function OverrideCreateForm({ onSubmit, onCancel }: OverrideCreateFormProps) {
  const [userId, setUserId] = useState('');
  const [featureKey, setFeatureKey] = useState<FeatureKey>('uploads');
  const [newLimit, setNewLimit] = useState('');
  const [reason, setReason] = useState('');
  const [duration, setDuration] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      userId,
      featureKey,
      newLimit: parseInt(newLimit, 10),
      reason,
      duration: duration || undefined,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 border rounded-lg bg-muted/50 space-y-4">
      <h4 className="font-medium">Create Override</h4>

      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <label className="text-sm font-medium">User ID</label>
          <Input
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder="user-123"
            className="mt-1"
          />
        </div>

        <div>
          <label className="text-sm font-medium">Feature</label>
          <select
            value={featureKey}
            onChange={(e) => setFeatureKey(e.target.value as FeatureKey)}
            className="w-full h-10 px-3 mt-1 rounded-md border bg-background"
          >
            {Object.keys(FEATURE_CONFIG).map((key) => (
              <option key={key} value={key}>
                {FEATURE_CONFIG[key as FeatureKey].name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-sm font-medium">New Limit</label>
          <Input
            type="number"
            value={newLimit}
            onChange={(e) => setNewLimit(e.target.value)}
            placeholder="100"
            className="mt-1"
          />
        </div>

        <div>
          <label className="text-sm font-medium">Duration (optional)</label>
          <Input
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
            placeholder="7d, 30d, 1h"
            className="mt-1"
          />
        </div>
      </div>

      <div>
        <label className="text-sm font-medium">Reason</label>
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Enter reason for override..."
          className="w-full h-20 px-3 py-2 mt-1 rounded-md border bg-background"
        />
      </div>

      <div className="flex justify-end gap-2">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit">
          Create Override
        </Button>
      </div>
    </form>
  );
}

interface OverrideCardProps {
  override: AdminQuotaOverride;
  onRevoke: () => void;
}

export function OverrideCard({ override, onRevoke }: OverrideCardProps) {
  const config = FEATURE_CONFIG[override.featureKey];
  const isExpired = override.expiresAt && new Date(override.expiresAt) < new Date();

  return (
    <div className={cn(
      'p-4 border rounded-lg',
      !override.isActive && 'opacity-50',
      isExpired && 'border-red-200 bg-red-50/50'
    )}>
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <div className={cn(
            'p-2 rounded-lg',
            override.isActive ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-600'
          )}>
            {override.isActive ? <CheckCircle className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="font-medium">{config?.name}</h4>
              <Badge variant="outline" className="text-xs">
                {override.isActive ? 'Active' : 'Revoked'}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground">
              User: {override.userId}
            </p>
            <div className="flex items-center gap-4 mt-2 text-sm">
              <span>
                <span className="text-muted-foreground">Limit:</span>{' '}
                {override.newLimit}
              </span>
              {override.originalLimit && (
                <span className="text-muted-foreground line-through">
                  was: {override.originalLimit}
                </span>
              )}
            </div>
            <p className="text-sm mt-1">{override.reason}</p>
            <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
              <User className="w-3 h-3" />
              <span>by {override.grantedByName || override.grantedBy}</span>
              <span>•</span>
              <Clock className="w-3 h-3" />
              <span>{new Date(override.createdAt).toLocaleDateString()}</span>
            </div>
            {override.expiresAt && (
              <p className="text-xs mt-1 text-muted-foreground">
                Expires: {new Date(override.expiresAt).toLocaleDateString()}
              </p>
            )}
          </div>
        </div>
        {override.isActive && (
          <Button variant="ghost" size="sm" onClick={onRevoke} className="text-red-600">
            Revoke
          </Button>
        )}
      </div>
    </div>
  );
}

interface OverrideSearchProps {
  className?: string;
}

export function OverrideSearch({ className }: OverrideSearchProps) {
  const { overrides } = useAdminOverride();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterFeature, setFilterFeature] = useState<string>('');

  const filteredOverrides = overrides.filter((override) => {
    const matchesSearch = override.userId.toLowerCase().includes(searchQuery.toLowerCase()) ||
      override.reason.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFeature = !filterFeature || override.featureKey === filterFeature;
    return matchesSearch && matchesFeature;
  });

  return (
    <Card className={cn(className)}>
      <CardHeader>
        <CardTitle>Override History</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search overrides..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <select
            className="h-10 px-3 rounded-md border bg-background text-sm"
            value={filterFeature}
            onChange={(e) => setFilterFeature(e.target.value)}
          >
            <option value="">All Features</option>
            {Object.keys(FEATURE_CONFIG).map((key) => (
              <option key={key} value={key}>
                {FEATURE_CONFIG[key as FeatureKey].name}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-2">
          {filteredOverrides.map((override) => (
            <div key={override.id} className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center gap-3">
                <Badge variant="outline">
                  {override.featureKey}
                </Badge>
                <span className="text-sm">{override.userId}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">{override.newLimit}</span>
                <Badge variant={override.isActive ? 'default' : 'secondary'}>
                  {override.isActive ? 'Active' : 'Revoked'}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export default AdminOverridePanel;
'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  CreditCard,
  Plus,
  Trash2,
  Check,
  Clock,
  AlertCircle,
  Download,
  ExternalLink,
  Star,
} from 'lucide-react';
import { Invoice, PaymentMethod, InvoiceStatus, PaymentMethodType } from '../types';
import { formatCurrency, formatDate, INVOICE_STATUS_COLORS } from '../constants';
import { useBillingApi } from '@/hooks/use-billing';
import { useBillingStore } from '../store';
import { cn } from '@/lib/utils';

interface BillingHistoryProps {
  className?: string;
}

export function BillingHistory({ className }: BillingHistoryProps) {
  const { invoices, isLoading } = useBillingStore();
  const [filterStatus, setFilterStatus] = useState<InvoiceStatus | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredInvoices = invoices.filter(invoice => {
    const matchesStatus = filterStatus === 'all' || invoice.status === filterStatus;
    const matchesSearch = invoice.invoiceNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
      invoice.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const getStatusIcon = (status: InvoiceStatus) => {
    switch (status) {
      case 'paid':
        return <Check className="w-4 h-4 text-green-600" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-600" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <Card className={cn(className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Billing History</CardTitle>
            <CardDescription>View and download your invoices</CardDescription>
          </div>
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Download All
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="flex items-center gap-4">
          <Input
            placeholder="Search invoices..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="max-w-xs"
          />
          <select
            className="h-10 px-3 rounded-md border bg-background text-sm"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as InvoiceStatus | 'all')}
          >
            <option value="all">All Status</option>
            <option value="paid">Paid</option>
            <option value="pending">Pending</option>
            <option value="failed">Failed</option>
            <option value="refunded">Refunded</option>
          </select>
        </div>

        <div className="space-y-2">
          {filteredInvoices.map((invoice) => (
            <div
              key={invoice.id}
              className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center gap-4">
                <div className={cn(
                  'w-10 h-10 rounded-full flex items-center justify-center',
                  invoice.status === 'paid' && 'bg-green-100',
                  invoice.status === 'pending' && 'bg-yellow-100',
                  invoice.status === 'failed' && 'bg-red-100'
                )}>
                  {getStatusIcon(invoice.status)}
                </div>
                <div>
                  <p className="font-medium">{invoice.description}</p>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <span>{invoice.invoiceNumber}</span>
                    <span>•</span>
                    <span>{formatDate(invoice.createdAt)}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="text-right">
                  <p className="font-semibold">{formatCurrency(invoice.amount, invoice.currency)}</p>
                  <Badge className={INVOICE_STATUS_COLORS[invoice.status as keyof typeof INVOICE_STATUS_COLORS]}>
                    {invoice.status}
                  </Badge>
                </div>
                <div className="flex items-center gap-1">
                  <Button variant="ghost" size="sm">
                    <Download className="w-4 h-4" />
                  </Button>
                  <Button variant="ghost" size="sm">
                    <ExternalLink className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {filteredInvoices.length === 0 && (
          <div className="text-center py-8 text-muted-foreground">
            No invoices found
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface PaymentMethodsCardProps {
  className?: string;
}

export function PaymentMethodsCard({ className }: PaymentMethodsCardProps) {
  const { paymentMethods, isProcessing } = useBillingStore();
  const { updatePaymentMethod, removePaymentMethod } = useBillingApi();
  const [showAddForm, setShowAddForm] = useState(false);

  const getCardIcon = (brand?: string) => {
    return <CreditCard className="w-5 h-5" />;
  };

  return (
    <Card className={cn(className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Payment Methods</CardTitle>
            <CardDescription>Manage your payment methods</CardDescription>
          </div>
          <Button size="sm" onClick={() => setShowAddForm(!showAddForm)}>
            <Plus className="w-4 h-4 mr-2" />
            Add Card
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {showAddForm && (
          <div className="p-4 border rounded-lg bg-muted/50 space-y-4">
            <div className="grid gap-4">
              <Input placeholder="Card Number" />
              <div className="grid grid-cols-2 gap-4">
                <Input placeholder="MM/YY" />
                <Input placeholder="CVC" />
              </div>
              <Input placeholder="Cardholder Name" />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowAddForm(false)}>
                Cancel
              </Button>
              <Button>Add Card</Button>
            </div>
          </div>
        )}

        <div className="space-y-2">
          {paymentMethods.map((method) => (
            <div
              key={method.id}
              className="flex items-center justify-between p-4 border rounded-lg"
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-8 bg-muted rounded flex items-center justify-center">
                  {getCardIcon(method.brand)}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-medium">
                      {method.brand?.charAt(0).toUpperCase()}{method.brand?.slice(1)} ****{method.last4}
                    </p>
                    {method.isDefault && (
                      <Badge variant="secondary" className="text-xs">Default</Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Expires {method.expiryMonth}/{method.expiryYear}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {!method.isDefault && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => updatePaymentMethod(method.id, true)}
                    disabled={isProcessing}
                  >
                    Set Default
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removePaymentMethod(method.id)}
                  disabled={isProcessing}
                  className="text-red-600 hover:text-red-700"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

interface UpcomingBillingCardProps {
  className?: string;
}

export function UpcomingBillingCard({ className }: UpcomingBillingCardProps) {
  const { currentSubscription } = useBillingStore();

  if (!currentSubscription) return null;

  const nextBillingDate = new Date(currentSubscription.currentPeriodEnd);
  const daysUntil = Math.ceil((nextBillingDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24));
  const amount = currentSubscription.billingInterval === 'monthly'
    ? currentSubscription.plan?.priceMonthly || 0
    : currentSubscription.plan?.priceAnnual || 0;

  return (
    <Card className={cn(className)}>
      <CardHeader>
        <CardTitle>Upcoming Billing</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
          <div>
            <p className="text-2xl font-bold">{formatCurrency(amount)}</p>
            <p className="text-sm text-muted-foreground">
              {currentSubscription.billingInterval === 'monthly' ? 'Monthly' : 'Annual'} payment
            </p>
          </div>
          <div className="text-right">
            <p className="text-lg font-semibold">{nextBillingDate.toLocaleDateString()}</p>
            <p className={cn(
              'text-sm',
              daysUntil <= 3 ? 'text-red-600' : 'text-muted-foreground'
            )}>
              in {daysUntil} days
            </p>
          </div>
        </div>

        <div className="mt-4 flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Payment method: ****{paymentMethods[0]?.last4 || 'N/A'}
          </p>
          <Button variant="link" size="sm">
            Update Payment Method
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default BillingHistory;

const paymentMethods = [];
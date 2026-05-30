'use client';

import { useEffect, useMemo, useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  ChevronsUpDown,
  FileIcon,
  MoreHorizontal,
  RefreshCw,
  Trash2,
  Archive,
  RotateCcw,
  Download,
  Eye,
  X,
  Search,
  Filter,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton, TableRowSkeleton } from '@/components/design-system/skeleton';
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination';
import { StatusBadge } from './status-badge';
import { useDocumentStore, Document, DocumentStatus } from '@/stores/document-store';
import { useDocumentsApi } from '@/hooks/use-documents';
import { appToast } from '@/lib/app-toast';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface Column {
  key: keyof Document;
  label: string;
  sortable?: boolean;
  className?: string;
}

const columns: Column[] = [
  { key: 'name', label: 'Name', sortable: true, className: 'min-w-[200px]' },
  { key: 'file_type', label: 'Type', sortable: true, className: 'w-[80px]' },
  { key: 'file_size', label: 'Size', sortable: true, className: 'w-[100px]' },
  { key: 'processing_status', label: 'Status', sortable: true, className: 'w-[130px]' },
  { key: 'folder', label: 'Folder', sortable: true, className: 'w-[120px]' },
  { key: 'created_at', label: 'Created', sortable: true, className: 'w-[150px]' },
];

const STATUS_OPTIONS: { value: DocumentStatus; label: string }[] = [
  { value: 'uploaded', label: 'Uploaded' },
  { value: 'processing', label: 'Processing' },
  { value: 'retrying', label: 'Retrying' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
  { value: 'needs_review', label: 'Needs Review' },
];

export function DocumentTable() {
  const store = useDocumentStore();
  const {
    fetchDocuments,
    deleteDocument,
    retryDocuments,
    batchArchive,
    batchRestore,
    batchDelete,
    loading,
  } = useDocumentsApi();

  const [showFilters, setShowFilters] = useState(false);
  const startRow = (store.pagination.page - 1) * store.pagination.limit + 1;
  const endRow = Math.min(store.pagination.page * store.pagination.limit, store.pagination.total);

  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments, store.filters, store.pagination.page, store.pagination.limit]);

  const handleSort = (key: keyof Document) => {
    if (store.filters.sort_by === key) {
      store.setFilters({
        sort_order: store.filters.sort_order === 'asc' ? 'desc' : 'asc',
      });
    } else {
      store.setFilters({ sort_by: key as never, sort_order: 'desc' });
    }
  };

  const getSortIcon = (key: keyof Document) => {
    if (store.filters.sort_by !== key) return <ChevronsUpDown className="h-4 w-4" />;
    return store.filters.sort_order === 'asc'
      ? <ChevronUp className="h-4 w-4" />
      : <ChevronDown className="h-4 w-4" />;
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const formatDate = (dateStr: string): string => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    try {
      await deleteDocument(id);
    } catch (err: unknown) {
      appToast.error(err instanceof Error ? err.message : 'Failed to delete document');
    }
  };

  const handleRetry = async (id: string) => {
    try {
      await retryDocuments([id]);
    } catch (err: unknown) {
      appToast.error(err instanceof Error ? err.message : 'Failed to retry document');
    }
  };

  const allSelected = store.documents.length > 0 &&
    store.selectedDocuments.length === store.documents.length;

  const handleSelectAll = () => {
    if (allSelected) {
      store.clearSelection();
    } else {
      store.selectAll();
    }
  };

  const handleStatusFilter = (status: DocumentStatus) => {
    const current = store.filters.status;
    const updated = current.includes(status)
      ? current.filter((s) => s !== status)
      : [...current, status];
    store.setFilters({ status: updated });
  };

  const fileTypes = useMemo(() => {
    const types = new Set(store.documents.map((d) => d.file_type));
    return Array.from(types).sort();
  }, [store.documents]);

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <div className="relative flex-1 sm:w-64">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search documents..."
              value={store.filters.search}
              onChange={(e) => store.setFilters({ search: e.target.value })}
              className="pl-9"
            />
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
            className="gap-2"
          >
            <Filter className="h-4 w-4" />
            Filters
            {store.filters.status.length > 0 && (
              <span className="ml-1 rounded-full bg-primary px-1.5 py-0.5 text-xs text-primary-foreground">
                {store.filters.status.length}
              </span>
            )}
          </Button>
        </div>

        {store.selectedDocuments.length > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              {store.selectedDocuments.length} selected
            </span>
            <Button size="sm" variant="outline" onClick={() => batchArchive(store.selectedDocuments)}>
              <Archive className="mr-2 h-4 w-4" />
              Archive
            </Button>
            <Button size="sm" variant="outline" onClick={() => batchRestore(store.selectedDocuments)}>
              <RotateCcw className="mr-2 h-4 w-4" />
              Restore
            </Button>
            <Button
              size="sm"
              variant="destructive"
              onClick={() => {
                if (confirm(`Delete ${store.selectedDocuments.length} documents?`)) {
                  batchDelete(store.selectedDocuments);
                }
              }}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </Button>
          </div>
        )}
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="rounded-lg border bg-card p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium">Filters</h3>
            <Button size="sm" variant="ghost" onClick={() => store.resetFilters()}>
              Reset all
            </Button>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-2">
              <label className="text-xs font-medium text-muted-foreground">Status</label>
              <div className="flex flex-wrap gap-1">
                {STATUS_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => handleStatusFilter(opt.value)}
                    className={cn(
                      'rounded-full px-2.5 py-1 text-xs transition-colors',
                      store.filters.status.includes(opt.value)
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted hover:bg-muted/80'
                    )}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-medium text-muted-foreground">File Type</label>
              <div className="flex flex-wrap gap-1">
                {fileTypes.map((type) => (
                  <button
                    key={type}
                    onClick={() => {
                      const updated = selectedTypes.includes(type)
                        ? selectedTypes.filter((t) => t !== type)
                        : [...selectedTypes, type];
                      setSelectedTypes(updated);
                      store.setFilters({ file_type: updated });
                    }}
                    className={cn(
                      'rounded-full px-2.5 py-1 text-xs uppercase transition-colors',
                      selectedTypes.includes(type)
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted hover:bg-muted/80'
                    )}
                  >
                    {type}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-medium text-muted-foreground">Date From</label>
              <Input
                type="date"
                value={store.filters.date_from}
                onChange={(e) => store.setFilters({ date_from: e.target.value })}
                className="text-sm"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-medium text-muted-foreground">Date To</label>
              <Input
                type="date"
                value={store.filters.date_to}
                onChange={(e) => store.setFilters({ date_to: e.target.value })}
                className="text-sm"
              />
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="table-wrap smooth-layout overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="w-[40px] px-3 py-3">
                  <input
                    aria-label="Select all documents"
                    type="checkbox"
                    checked={allSelected}
                    onChange={handleSelectAll}
                    className="h-4 w-4 rounded border-input"
                  />
                </th>
                {columns.map((col) => (
                  <th
                    key={col.key}
                    className={cn('px-3 py-3 text-left text-xs font-medium text-muted-foreground', col.className)}
                  >
                    {col.sortable ? (
                      <button
                        onClick={() => handleSort(col.key)}
                        className="inline-flex items-center gap-1 hover:text-foreground"
                      >
                        {col.label}
                        {getSortIcon(col.key)}
                      </button>
                    ) : (
                      col.label
                    )}
                  </th>
                ))}
                <th className="w-[50px] px-3 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {loading && store.documents.length === 0 ? (
                <tr>
                  <td colSpan={columns.length + 2} className="px-3 py-6">
                    <div className="space-y-2">
                      <Skeleton className="h-4 w-48" />
                      <table className="w-full">
                        <tbody>
                          <TableRowSkeleton cols={columns.length + 2} />
                          <TableRowSkeleton cols={columns.length + 2} />
                          <TableRowSkeleton cols={columns.length + 2} />
                        </tbody>
                      </table>
                    </div>
                  </td>
                </tr>
              ) : store.documents.length === 0 ? (
                <tr>
                  <td colSpan={columns.length + 2} className="px-3 py-12 text-center text-muted-foreground">
                    No documents found
                  </td>
                </tr>
              ) : (
                store.documents.map((doc) => (
                  <DocumentRow
                    key={doc.id}
                    document={doc}
                    isSelected={store.selectedDocuments.includes(doc.id)}
                    onToggleSelect={() => store.toggleSelect(doc.id)}
                    onDelete={() => handleDelete(doc.id)}
                    onRetry={() => handleRetry(doc.id)}
                    onArchive={() => batchArchive([doc.id])}
                    formatFileSize={formatFileSize}
                    formatDate={formatDate}
                    loading={loading}
                  />
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {store.pagination.pages > 1 && (
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {startRow} to {endRow} of {store.pagination.total} documents
          </p>
          <Pagination className="mx-0 w-auto justify-start sm:justify-end">
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious
                  onClick={() => store.setPage(store.pagination.page - 1)}
                  disabled={loading || store.pagination.page === 1}
                />
              </PaginationItem>
              <PaginationItem>
                <PaginationLink isActive>
                  {store.pagination.page}/{store.pagination.pages}
                </PaginationLink>
              </PaginationItem>
              <PaginationItem>
                <PaginationNext
                  onClick={() => store.setPage(store.pagination.page + 1)}
                  disabled={loading || store.pagination.page >= store.pagination.pages}
                />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        </div>
      )}
    </div>
  );
}

interface DocumentRowProps {
  document: Document;
  isSelected: boolean;
  onToggleSelect: () => void;
  onDelete: () => void;
  onRetry: () => void;
  onArchive: () => void;
  formatFileSize: (bytes: number) => string;
  formatDate: (date: string) => string;
  loading: boolean;
}

function DocumentRow({
  document,
  isSelected,
  onToggleSelect,
  onDelete,
  onRetry,
  onArchive,
  formatFileSize,
  formatDate,
  loading,
}: DocumentRowProps) {
  const getFileIcon = (type: string) => {
    const iconMap: Record<string, string> = {
      pdf: '📄',
      doc: '📝',
      docx: '📝',
      xls: '📊',
      xlsx: '📊',
      png: '🖼️',
      jpg: '🖼️',
      jpeg: '🖼️',
      gif: '🖼️',
      txt: '📃',
      csv: '📑',
    };
    return iconMap[type.toLowerCase()] || '📎';
  };

  return (
    <tr className={cn('hover:bg-muted/50 transition-colors', isSelected && 'bg-muted/30')}>
      <td className="px-3 py-3">
        <input
          aria-label={`Select ${document.name}`}
          type="checkbox"
          checked={isSelected}
          onChange={onToggleSelect}
          className="h-4 w-4 rounded border-input"
        />
      </td>
      <td className="px-3 py-3">
        <div className="flex items-center gap-2">
          <span className="text-lg">{getFileIcon(document.file_type)}</span>
          <div className="min-w-0">
            <p className="truncate text-sm font-medium">{document.name}</p>
            <p className="truncate text-xs text-muted-foreground">{document.file_name}</p>
          </div>
        </div>
      </td>
      <td className="px-3 py-3">
        <span className="text-xs uppercase font-medium text-muted-foreground">
          {document.file_type}
        </span>
      </td>
      <td className="px-3 py-3 text-sm">{formatFileSize(document.file_size)}</td>
      <td className="px-3 py-3">
        <div className="flex items-center gap-2">
          <StatusBadge status={document.processing_status} />
          {document.retry_count > 0 && (
            <span className="text-xs text-muted-foreground">
              ({document.retry_count} retries)
            </span>
          )}
        </div>
      </td>
      <td className="px-3 py-3 text-sm text-muted-foreground">
        {document.folder || '-'}
      </td>
      <td className="px-3 py-3 text-sm text-muted-foreground">
        {formatDate(document.created_at)}
      </td>
      <td className="px-3 py-3">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-[160px]">
            <DropdownMenuItem disabled={document.processing_status === 'completed'}>
              <Download className="mr-2 h-4 w-4" />
              Download
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Eye className="mr-2 h-4 w-4" />
              View details
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            {document.processing_status === 'failed' && (
              <DropdownMenuItem onClick={onRetry}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Retry
              </DropdownMenuItem>
            )}
            <DropdownMenuItem onClick={onArchive}>
              <Archive className="mr-2 h-4 w-4" />
              Archive
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={onDelete} className="text-destructive">
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </td>
    </tr>
  );
}